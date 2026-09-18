"""
Database Connection and Initialization Manager.
Supports MySQL 8.0+ with seamless zero-configuration fallback to SQLite.
"""

import os
import time
import sqlite3
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configuration from Environment or defaults
# Configuration from Streamlit Secrets or Environment
# Configuration from Streamlit Secrets or Environment
try:
    import streamlit as st
    HAS_TIDB_SECRETS = "mysql" in st.secrets
    if HAS_TIDB_SECRETS:
        DB_CONFIG = dict(st.secrets["mysql"])
    else:
        DB_CONFIG = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "hr_management")
        }
except Exception:
    HAS_TIDB_SECRETS = False
    DB_CONFIG = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "hr_management")
    }

_cached_status: Optional[Dict[str, Any]] = None
_last_status_check: float = 0
STATUS_CACHE_TTL = 30.0  # seconds

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "sql", "01_schema.sql")
SEED_PATH = os.path.join(PROJECT_ROOT, "sql", "02_seed_data.sql")
SQLITE_DB_PATH = os.path.join(PROJECT_ROOT, "database", "hr_management_portable.db")


def try_connect_mysql(config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """Attempt connecting to MySQL server and ensure database & tables exist."""
    global DB_CONFIG, _cached_status, _last_status_check
    cfg = config or DB_CONFIG
    try:
        import pymysql
        # Step 1: Connect to server without database
        conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            connect_timeout=1,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` DEFAULT CHARACTER SET utf8mb4;")
        conn.close()

        # Step 2: Connect to the specific database
        conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            connect_timeout=1,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

        # Check if tables exist; initialize schema+seed on a fresh/empty database
        init_errors: List[str] = []
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES;")
            tables = cur.fetchall()
            if len(tables) < 12:
                init_errors = _initialize_mysql_db(conn)
                cur.execute("SHOW TABLES;")
                tables = cur.fetchall()

        conn.close()

        # Don't report success if initialization was supposed to create the
        # 12-table schema but didn't actually get there.
        if len(tables) < 12:
            detail = "; ".join(init_errors[:3]) if init_errors else "no tables were created and no SQL errors were reported"
            _cached_status = {
                "engine": "SQLite (Dual Engine Fallback)",
                "is_mysql": False,
                "status": "MySQL Offline — Running on Embedded Portable Engine",
                "details": f"Local database: {os.path.basename(SQLITE_DB_PATH)}",
                "error": f"MySQL schema initialization incomplete ({len(tables)}/12 tables): {detail}",
                "color": "orange"
            }
            _last_status_check = time.time()
            return False, f"Connected to MySQL, but schema setup failed ({len(tables)}/12 tables created): {detail}"

        DB_CONFIG = cfg
        _cached_status = {
            "engine": "MySQL 8.0+",
            "is_mysql": True,
            "status": "Connected (Live MySQL)",
            "details": f"{cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']}",
            "color": "green"
        }
        _last_status_check = time.time()
        return True, f"Successfully connected to MySQL at {cfg['host']}:{cfg['port']}"
    except Exception as e:
        _cached_status = {
            "engine": "SQLite (Dual Engine Fallback)",
            "is_mysql": False,
            "status": "MySQL Offline — Running on Embedded Portable Engine",
            "details": f"Local database: {os.path.basename(SQLITE_DB_PATH)}",
            "error": str(e),
            "color": "orange"
        }
        _last_status_check = time.time()
        return False, f"MySQL connection failed: {str(e)}"


def _split_sql_statements(text: str) -> List[str]:
    """Splits a SQL script into individual statements on ';', respecting
    single-quoted string literals.

    A naive `text.split(";")` breaks as soon as any stored VARCHAR/TEXT value
    happens to contain a semicolon (e.g. a review comment like 'Good work;
    keep it up.') -- it chops one INSERT statement into two invalid
    fragments and both fail. This walks the text and only treats ';' as a
    separator when not inside a quoted string, and treats '' as an escaped
    quote inside a string per standard SQL.
    """
    statements: List[str] = []
    current: List[str] = []
    in_string = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "'":
            if in_string and i + 1 < n and text[i + 1] == "'":
                current.append("''")
                i += 2
                continue
            in_string = not in_string
            current.append(ch)
            i += 1
            continue
        if ch == ";" and not in_string:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _strip_sql_line_comments(text: str) -> str:
    """Removes '--' line comments before statement splitting.

    Without this, a leading comment block (e.g. a file header) stays glued
    to the next real statement when the file is split on ';'. That made the
    "skip DROP DATABASE / CREATE DATABASE / USE" guard below silently fail
    to match (the chunk started with '--', not 'DROP DATABASE'), so the
    schema file's own `DROP DATABASE IF EXISTS hr_management;` line was
    actually being executed against the live connection -- immediately
    wiping out the database this function was in the middle of populating.
    """
    kept_lines = [line for line in text.splitlines() if not line.strip().startswith("--")]
    return "\n".join(kept_lines)


def _initialize_mysql_db(conn) -> List[str]:
    """Executes schema and seed scripts on MySQL connection.

    Returns a list of human-readable errors for any statement that failed,
    so callers can surface real problems instead of assuming success.
    """
    errors: List[str] = []
    with conn.cursor() as cur:
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                content = _strip_sql_line_comments(f.read())
                statements = _split_sql_statements(content)
                for stmt in statements:
                    if stmt.upper().startswith("DROP DATABASE") or stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                        continue
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        errors.append(f"[schema] {stmt[:60]}... -> {e}")

        if os.path.exists(SEED_PATH):
            with open(SEED_PATH, "r", encoding="utf-8") as f:
                content = _strip_sql_line_comments(f.read())
                statements = _split_sql_statements(content)
                for stmt in statements:
                    if stmt.upper().startswith("USE "):
                        continue
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        errors.append(f"[seed] {stmt[:60]}... -> {e}")
    return errors


def _init_sqlite_db():
    """Initializes a local SQLite database matching the 12-table schema and seeds it."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()

    sqlite_ddl = """
    CREATE TABLE IF NOT EXISTS hr_manager (
        hr_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hr_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone_number TEXT NOT NULL,
        designation TEXT NOT NULL,
        experience_years INTEGER NOT NULL CHECK (experience_years >= 0)
    );

    CREATE TABLE IF NOT EXISTS department (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL UNIQUE,
        location TEXT NOT NULL,
        budget REAL NOT NULL CHECK (budget >= 0),
        manager_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS employee (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        gender TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone_number TEXT NOT NULL,
        address TEXT NOT NULL,
        hire_date TEXT NOT NULL,
        salary REAL NOT NULL CHECK (salary > 0),
        job_title TEXT NOT NULL,
        department_id INTEGER NOT NULL REFERENCES department(department_id) ON UPDATE CASCADE ON DELETE RESTRICT,
        hr_id INTEGER NOT NULL REFERENCES hr_manager(hr_id) ON UPDATE CASCADE ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS project (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        budget REAL NOT NULL CHECK (budget >= 0),
        client_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Planning',
        department_id INTEGER NOT NULL REFERENCES department(department_id) ON UPDATE CASCADE ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS employee_project (
        employee_id INTEGER NOT NULL REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE CASCADE,
        project_id INTEGER NOT NULL REFERENCES project(project_id) ON UPDATE CASCADE ON DELETE CASCADE,
        assigned_date TEXT NOT NULL,
        employee_role TEXT NOT NULL,
        hours_worked REAL NOT NULL DEFAULT 0.00 CHECK (hours_worked >= 0),
        PRIMARY KEY (employee_id, project_id)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE CASCADE,
        date TEXT NOT NULL,
        check_in_time TEXT,
        check_out_time TEXT,
        work_hours REAL DEFAULT 0.00,
        attendance_status TEXT NOT NULL DEFAULT 'Present',
        UNIQUE (employee_id, date)
    );

    CREATE TABLE IF NOT EXISTS `leave` (
        leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE CASCADE,
        leave_type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        reason TEXT,
        approval_status TEXT NOT NULL DEFAULT 'Pending'
    );

    CREATE TABLE IF NOT EXISTS payroll (
        payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE CASCADE,
        basic_salary REAL NOT NULL,
        allowances REAL NOT NULL DEFAULT 0.00,
        deductions REAL NOT NULL DEFAULT 0.00,
        net_salary REAL NOT NULL,
        payment_date TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS performance_review (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE CASCADE,
        reviewer_name TEXT NOT NULL,
        review_date TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        comments TEXT
    );

    CREATE TABLE IF NOT EXISTS training (
        training_id INTEGER PRIMARY KEY AUTOINCREMENT,
        training_name TEXT NOT NULL,
        trainer_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        training_type TEXT NOT NULL,
        cost REAL NOT NULL DEFAULT 0.00 CHECK (cost >= 0)
    );

    CREATE TABLE IF NOT EXISTS employee_training (
        employee_id INTEGER NOT NULL REFERENCES employee(employee_id) ON UPDATE CASCADE ON DELETE CASCADE,
        training_id INTEGER NOT NULL REFERENCES training(training_id) ON UPDATE CASCADE ON DELETE CASCADE,
        completion_status TEXT NOT NULL DEFAULT 'Enrolled',
        score REAL CHECK (score BETWEEN 0.00 AND 100.00),
        PRIMARY KEY (employee_id, training_id)
    );

    CREATE TABLE IF NOT EXISTS recruitment (
        recruitment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT NOT NULL,
        position_applied TEXT NOT NULL,
        interview_date TEXT NOT NULL,
        interview_status TEXT NOT NULL DEFAULT 'Scheduled',
        offer_status TEXT NOT NULL DEFAULT 'Pending',
        hr_id INTEGER NOT NULL REFERENCES hr_manager(hr_id) ON UPDATE CASCADE ON DELETE RESTRICT
    );
    """
    cur.executescript(sqlite_ddl)
    conn.commit()

    # Seed if empty
    cur.execute("SELECT COUNT(*) FROM employee")
    if cur.fetchone()[0] == 0 and os.path.exists(SEED_PATH):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            clean_lines = []
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("--") or stripped.upper().startswith("USE "):
                    continue
                clean_lines.append(line)
            clean_sql = "\n".join(clean_lines)
            try:
                cur.executescript(clean_sql)
                conn.commit()
            except Exception:
                pass
    conn.close()


def get_connection_status(force_recheck: bool = False) -> Dict[str, Any]:
    """Returns cached or refreshed connection status."""
    global _cached_status, _last_status_check
    now = time.time()
    if _cached_status is None or force_recheck or (now - _last_status_check > STATUS_CACHE_TTL):
        try_connect_mysql()
    return _cached_status


def run_query(query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """Executes a SELECT query and returns a pandas DataFrame."""
    status = get_connection_status()
    if status["is_mysql"]:
        import pymysql
        # NOTE: intentionally NOT using cursorclass=DictCursor here.
        # pandas.read_sql() with a raw DBAPI2 connection assumes each fetched
        # row is a plain tuple/sequence; with pymysql's DictCursor each row
        # is a dict instead, and pandas ends up reading dict.keys() as the
        # row values -- every returned "row" becomes the column names
        # repeated, silently corrupting every chart/table/KPI in the app.
        # The default tuple cursor gives pandas real values.
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        try:
            return pd.read_sql(query, conn, params=params)
        finally:
            conn.close()
    else:
        _init_sqlite_db()
        conn = sqlite3.connect(SQLITE_DB_PATH)
        try:
            # SQLite string concatenation compatibility
            adapted_query = query.replace("CONCAT(e.first_name, ' ', e.last_name)", "(e.first_name || ' ' || e.last_name)")
            # SQLite uses '?' placeholders, not MySQL-style '%s'
            adapted_query = adapted_query.replace("%s", "?")
            return pd.read_sql(adapted_query, conn, params=params)
        finally:
            conn.close()


def execute_action(query: str, params: Optional[Tuple] = None) -> Tuple[bool, str]:
    """Executes an INSERT, UPDATE, or DELETE statement with commit."""
    status = get_connection_status()
    if status["is_mysql"]:
        import pymysql
        try:
            conn = pymysql.connect(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                autocommit=True
            )
            with conn.cursor() as cur:
                cur.execute(query, params or ())
            conn.close()
            return True, "Executed successfully in MySQL database."
        except Exception as e:
            return False, f"MySQL Error: {str(e)}"
    else:
        _init_sqlite_db()
        try:
            conn = sqlite3.connect(SQLITE_DB_PATH)
            cur = conn.cursor()
            adapted_query = query.replace("%s", "?")
            cur.execute(adapted_query, params or ())
            conn.commit()
            conn.close()
            return True, "Executed successfully in portable local database."
        except Exception as e:
            return False, f"Database Error: {str(e)}"
