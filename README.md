# 🏢 Employee & HR Management Dashboard

## 🚀 Live Application

**Try the deployed application:**

👉 https://employee-and-hr-management-dashboard-wknmafdgk77vpdpfecrwwr.streamlit.app/

The application is deployed using **Streamlit Community Cloud** and connects to a **TiDB Cloud MySQL-compatible database**.

---

## 📊 Overview

The Employee & HR Management Dashboard is a centralized platform for managing and analysing employee and HR data.

The system combines:

* 🐍 Python application development
* 🎈 Streamlit interactive dashboards
* 🐬 MySQL-compatible relational database
* ☁️ TiDB Cloud database hosting
* 📈 Plotly data visualization
* 🐼 Pandas data processing
* 🔎 Interactive SQL querying
* 🗃️ Normalized relational database design
* 📚 3NF and functional-dependency documentation

The database is designed around **Third Normal Form (3NF)** with clearly defined relationships, primary keys, foreign keys, and bridge tables.

---

## ✨ Features

| Module                 | Functionality                                     |
| ---------------------- | ------------------------------------------------- |
| 📊 Overview            | Executive HR metrics and analytics                |
| 👥 Employees           | Employee records, search, filtering and CRUD      |
| 🏛️ Departments        | Department information and budget analysis        |
| 💼 Projects            | Projects, staffing and employee assignments       |
| ⏱️ Attendance          | Attendance tracking and analysis                  |
| 🏖️ Leave              | Leave requests and status analysis                |
| 💰 Payroll             | Salary, allowances, deductions and reconciliation |
| 🌟 Performance         | Performance reviews and rating analysis           |
| 🎓 Training            | Training programs and employee participation      |
| 🎯 Recruitment         | Candidate tracking and recruitment funnel         |
| 🗄️ Schema Explorer    | Explore database structure                        |
| ⚡ SQL Studio           | Execute and analyse SQL queries                   |
| 📈 Reports             | HR reporting and data export                      |
| 📜 3NF Documentation   | Normalization and functional dependencies         |
| ⚙️ Database Connection | MySQL/TiDB connection management                  |

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │       User / HR     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Streamlit Dashboard │
                    │       app.py        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Database Connection │
                    │   connection.py     │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │   TiDB Cloud    │        │      SQLite     │
        │ MySQL-Compatible│        │ Portable Fallback│
        │   Production    │        │ Local / Offline │
        └────────┬────────┘        └─────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ HR Management Data  │
        │                     │
        │ Employee            │
        │ Department          │
        │ Project             │
        │ Attendance          │
        │ Leave               │
        │ Payroll             │
        │ Performance         │
        │ Training            │
        │ Recruitment         │
        └─────────────────────┘
```

---

## 🗃️ Database Design

The system contains **12 relational entities**:

```text
HR_MANAGER
DEPARTMENT
EMPLOYEE
PROJECT
EMPLOYEE_PROJECT
ATTENDANCE
LEAVE
PAYROLL
PERFORMANCE_REVIEW
TRAINING
EMPLOYEE_TRAINING
RECRUITMENT
```

The database uses:

* Primary keys
* Foreign keys
* Referential integrity
* One-to-many relationships
* Many-to-many relationships
* Bridge tables
* Functional dependencies
* 1NF
* 2NF
* 3NF

### Example relationship

```text
DEPARTMENT
     │
     │ 1:M
     ▼
EMPLOYEE
   │ │ │
   │ │ └──────── PAYROLL
   │ └────────── LEAVE
   └──────────── ATTENDANCE

EMPLOYEE
   │
   ├──────── EMPLOYEE_PROJECT ─────── PROJECT
   │
   └──────── EMPLOYEE_TRAINING ───── TRAINING
```

---

## 🛠️ Technology Stack

| Technology                | Purpose                           |
| ------------------------- | --------------------------------- |
| Python                    | Application logic                 |
| Streamlit                 | Web application                   |
| MySQL                     | Relational database compatibility |
| TiDB Cloud                | Cloud database hosting            |
| SQLite                    | Portable fallback database        |
| Pandas                    | Data processing                   |
| Plotly                    | Data visualization                |
| PyMySQL                   | Database connectivity             |
| SQL                       | Database queries and analytics    |
| Git                       | Version control                   |
| GitHub                    | Source repository                 |
| Streamlit Community Cloud | Application deployment            |

---

## 📁 Project Structure

```text
Employee-and-HR-Management-Dashboard/
│
├── employee-hr-management-system/
│   │
│   ├── app.py
│   ├── requirements.txt
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── queries.py
│   │   └── hr_management_portable.db
│   │
│   ├── sql/
│   │   ├── 01_schema.sql
│   │   ├── 02_seed_data.sql
│   │   └── 03_complex_queries.sql
│   │
│   ├── docs/
│   │   ├── NORMALIZATION.md
│   │   ├── EER_DIAGRAM.md
│   │   └── ASSIGNMENT_REPORT.md
│   │
│   └── tests/
│       └── test_system.py
│
└── README.md
```

---

## ☁️ Cloud Deployment

The production application uses the following architecture:

```text
GitHub
   │
   ▼
Streamlit Community Cloud
   │
   │ Streamlit Secrets
   ▼
TiDB Cloud
   │
   ▼
hr_management
```

Database credentials are stored using **Streamlit Secrets** rather than committed to the repository.

Example configuration:

```toml
[mysql]
host = "your-database-host"
port = 4000
user = "your-database-user"
password = "your-database-password"
database = "hr_management"
```

> ⚠️ Never commit real database passwords or other credentials to GitHub.

---

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/an4848/Employee-and-HR-Management-Dashboard.git
cd Employee-and-HR-Management-Dashboard/employee-hr-management-system
```

### 2. Create a virtual environment

Windows:

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Streamlit

```bash
python -m streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

## 🐬 MySQL / TiDB Database

The application is compatible with MySQL-style relational databases.

For local development, you can use:

```text
Host: localhost
Port: 3306
Database: hr_management
```

For cloud deployment, the application can connect to a MySQL-compatible TiDB Cloud instance through Streamlit Secrets.

The SQL files required to create and populate the database are located in:

```text
sql/
├── 01_schema.sql
├── 02_seed_data.sql
└── 03_complex_queries.sql
```

---

## 🗄️ SQLite Portable Mode

The project also includes a portable SQLite database:

```text
database/hr_management_portable.db
```

SQLite fallback mode allows the application to run without a separate MySQL server.

This is useful for:

* Academic demonstrations
* Offline development
* Testing
* Quick setup
* Environments without MySQL

---

## ⚡ SQL Studio

The application includes an interactive SQL Studio.

It supports:

* Custom SQL queries
* Query execution
* Interactive result tables
* Predefined academic queries
* Data analysis

The project also contains complex SQL examples covering:

* `JOIN`
* `GROUP BY`
* Aggregation
* CTEs
* Window functions
* `DENSE_RANK()`
* Conditional aggregation
* Many-to-many relationships
* Salary analysis
* Recruitment analytics

---

## 📚 Database & Academic Documentation

Additional documentation is available in the `docs/` directory.

### Normalization

`docs/NORMALIZATION.md`

Covers:

* Functional dependencies
* Attribute mapping
* 1NF
* 2NF
* 3NF
* Normalization proof
* Armstrong's axioms

### EER Diagram

`docs/EER_DIAGRAM.md`

Documents:

* Entities
* Relationships
* Cardinalities
* Database structure

### Assignment Report

`docs/ASSIGNMENT_REPORT.md`

Contains the detailed academic documentation for the project.

---

## 🧪 Testing

System tests are available in:

```text
tests/test_system.py
```

Run:

```bash
python tests/test_system.py
```

Windows:

```bash
py tests/test_system.py
```

---

## 🔐 Security

Database credentials should **never** be committed to GitHub.

Use:

* Streamlit Secrets for Streamlit Cloud
* Environment variables for local development
* `.env` files locally when appropriate

Never publish:

```text
MYSQL_PASSWORD
database passwords
API keys
private credentials
```

---

## 🎯 Project Objectives

This project demonstrates practical knowledge of:

* Relational database design
* EER modelling
* Functional dependencies
* Database normalization
* SQL
* CRUD operations
* Primary and foreign keys
* Many-to-many relationships
* Python programming
* Streamlit application development
* Data visualization
* Cloud database connectivity
* Cloud application deployment
* Secure credential management

---

## 🚀 Live Demo

### Employee & HR Management Dashboard

**https://employee-and-hr-management-dashboard-wknmafdgk77vpdpfecrwwr.streamlit.app/**

The deployed application currently uses a cloud-hosted MySQL-compatible database through TiDB Cloud.

---

## 🤝 Contributing

Contributions and improvements are welcome.

If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the application
5. Submit a pull request

---

## ⭐ Support

If you find this project useful:

⭐ Star the repository
🍴 Fork the project
🐛 Report bugs
💡 Suggest improvements
🔧 Submit pull requests

---

## 📄 License

This project is available under the license included in the repository.

---

<p align="center">

**Built with 🐍 Python · 🎈 Streamlit · 🐬 MySQL · ☁️ TiDB Cloud**

</p>
