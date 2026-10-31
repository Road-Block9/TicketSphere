# CONTEXT.md — Project State & Continuity Document
**Project Title:** Customer Support Ticket Analytics and GenAI Business Assistant  
**Last Updated:** 2026-10-31  
**Project Lead / Mentee:** Corporate Training Capstone  

---

## 1. Project Overview and Capstone Requirements
### Problem Statement
Companies receive large volumes of customer support tickets across categories (deliveries, payment failures, refunds, damaged products, poor service). Support managers struggle to monitor unresolved tickets, track resolution times, spot recurring bottlenecks, and extract actionable operational decisions.

### Capstone Requirements
1. **Data Ingestion (File & API):** CSV upload and a documented API ingestion path (local/mock REST API fallback to avoid paid subscriptions).
2. **Data Transformation:** Python & Pandas for schema standardisation, deduplication, null handling, resolution time calculation, and a data quality report.
3. **Data Storage:** Relational storage in SQLite with duplicate prevention and clean schema design.
4. **SQL Analytics:** Analytical queries answering core business questions (volume, category breakdown, status distribution, average resolution time, high unresolved complaint categories, temporal trends).
5. **GenAI Assistant:** Grounded executive summaries & operational recommendations strictly using verified SQL metrics, with an honest template-based fallback if no API key is provided.
6. **Application Interface:** Clean, professional Streamlit web dashboard.

---

## 2. Architecture and Technology Stack
```
[ CSV File / REST API ]
          │
          ▼
[ Ingestion Layer (Python, Requests) ]
          │
          ▼
[ Transformation Layer (Pandas) ] ──▶ [ Data Quality Metrics ]
          │
          ▼
[ SQLite Database (customer_support.db) ]
          │
          ▼
[ SQL Analytics Engine (parameterised queries) ]
          │
    ┌─────┴──────────────────────────┐
    ▼                                ▼
[ Streamlit Visual Dashboard ]   [ GenAI Business Assistant ]
(Plotly charts & metrics)        (Executive Summary & Action Plan)
```

- **Language & Runtime:** Python 3.13+
- **Data Processing:** Pandas
- **Database:** SQLite3
- **Web UI & Visualization:** Streamlit, Plotly
- **API Ingestion:** Requests / FastAPI (or Flask/mock server for local API demonstration)
- **Generative AI:** Google Gemini API / OpenAI API client with deterministic fallback
- **Version Control & Quality:** Git, `.gitignore`, pytest, `.env` for secrets

---

## 3. Module Roadmap and Status

| Module | Title | Target Deliverable | Status |
| :--- | :--- | :--- | :--- |
| **Module 1** | Project Setup & Dataset Prep | Folder structure, venv, requirements.txt, sample CSV, data dictionary, inspection script | **TESTED** |
| **Module 2** | Data Ingestion (CSV File) | CSV file reader, validation, schema audit, empty/malformed handling | **TESTED** |
| **Module 3** | Data Transformation & Quality | Pandas cleaning, deduplication, resolution metrics, DQ report | **TESTED** |
| **Module 4** | Relational Database & Storage | SQLite schema, idempotent loader, duplicate prevention | **TESTED** |
| **Module 5** | SQL Analytics Queries | 7 business SQL queries, verification tests | NOT STARTED |
| **Module 6** | GenAI Business Assistant | Grounded prompt engineer, LLM integration & fallback reporter | NOT STARTED |
| **Module 7** | Streamlit Web Application | Multi-tab dashboard: Upload, DQ Report, Analytics, AI Report | NOT STARTED |
| **Module 8** | Testing, Documentation & Wrap-Up| Automated tests, README, presentation outline, final review | NOT STARTED |

---

## 4. Environment and Setup
- **Operating System:** Windows 10/11
- **Python Version:** 3.13.3
- **Git Version:** 2.54.0.windows.1
- **Working Directory:** `d:\A Capstone`
- **Virtual Environment:** `.venv` (created via `python -m venv .venv`, all dependencies installed and verified)

---

## 5. Dataset and Data Schema
### Target Unified Schema (`tickets`)
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `ticket_id` | TEXT / PRIMARY KEY | Unique ticket identifier (e.g., TKT-1001) |
| `customer_id` | TEXT | Anonymised customer ID (e.g., CUST-5021) |
| `created_at` | TIMESTAMP | ISO-8601 date-time of ticket creation |
| `resolved_at` | TIMESTAMP | Date-time of ticket resolution (NULL if open/pending) |
| `category` | TEXT | Complaint category (Delivery & Shipping, Billing & Refunds, Product Quality, Technical Support, Customer Service) |
| `priority` | TEXT | Critical, High, Medium, Low |
| `status` | TEXT | Open, Pending, Resolved, Closed |
| `subject` | TEXT | Short summary / issue title |
| `description` | TEXT | Detailed customer complaint text |
| `resolution_notes`| TEXT | Notes logged by support agent upon closure |
| `resolution_time_hours`| REAL / FLOAT | Calculated elapsed hours from created_at to resolved_at (NULL if unresolved) |
| `is_unresolved` | INTEGER | Derived boolean flag (1 if Open/Pending, 0 if Resolved/Closed) |
| `inserted_at` | TIMESTAMP | Audit timestamp when record was stored in SQLite |

---

## 6. Implemented Features and Important Files
- `CONTEXT.md`: Permanent continuity and state tracker.
- `.gitignore`: Configured to exclude `.venv/`, `__pycache__/`, `*.db`, `.env`, `.pytest_cache/`.
- `.env.example`: Configuration template for API keys, DB path, and mock API host/port.
- `requirements.txt`: Pinned dependencies for Pandas, Streamlit, Plotly, Requests, FastAPI, Uvicorn, pytest, google-genai.
- `data/DATA_DICTIONARY.md`: Complete column specifications, integrity rules, and mapping to 7 business questions.
- `data/raw/customer_support_tickets.csv`: 60 realistic ticket records with valid timestamps, categories, and resolution notes.
- `data/processed/customer_support.db`: Persistent SQLite database initialized with `tickets` and `ingestion_logs` tables.
- `scripts/generate_sample_dataset.py`: Generator script ensuring correct CSV standard escaping and quote wrapping.
- `scripts/inspect_dataset.py`: Verified dataset auditing script reporting shape, nulls, and distributions.
- `src/__init__.py`: Application source package marker.
- `src/ingestion.py`: Robust CSV reader and validator supporting file paths and Streamlit buffer uploads, column alias normalization, and error auditing.
- `src/transformation.py`: Comprehensive cleaning engine with duplicate removal, taxonomy standardisation, timestamp parsing, `resolution_time_hours` calculation, and a structured `DataQualityReport`.
- `src/database.py`: Database management module with SQLite schema initialization, transactional idempotent loader (`INSERT OR IGNORE`), duplicate prevention, and parameterised SQL query executor.
- `tests/__init__.py`: Test suite package marker.
- `tests/test_ingestion.py`: 7 automated pytest test cases covering file reading, validation, empty files, and buffer streams.
- `tests/test_transformation.py`: 9 automated pytest test cases covering deduplication, taxonomy mapping, duration math, and anomaly clearance.
- `tests/test_database.py`: 6 automated pytest test cases covering schema creation, duplicate prevention on repeated imports, data retrieval, and parameterised queries. (22 total tests across project).

---

## 7. Design Decisions and Their Reasons
1. **SQLite over complex DB engines:** Zero-setup, single-file relational database ideal for capstone review, reproducible across reviewer machines without installing PostgreSQL/MySQL services.
2. **Deterministic Fallback for GenAI:** In corporate reviews or offline demos where an external API key is invalid or rate-limited, the system seamlessly falls back to a template-driven analytical report without crashing or fabricating fake AI output.
3. **Local REST API Mock:** Zendesk and enterprise tools require paid accounts or business credit cards; a lightweight local mock server provides a real HTTP request/response pipeline matching the capstone requirement at zero cost.
4. **CSV Quoting Protocol:** Used Python `csv.writer` with `QUOTE_MINIMAL` to prevent commas inside ticket descriptions from breaking Pandas CSV tokenization.
5. **Polymorphic Ingestion Target (`str`, `Path`, `BytesIO`, `StringIO`):** Designed `read_csv_tickets` in `src/ingestion.py` to ingest from both filesystem paths and uploaded stream buffers, guaranteeing identical validation in the CLI and the Streamlit UI.
6. **No Fabricated Resolution Times:** Strictly set `resolution_time_hours` and `resolved_at` to `None`/`NaN` for Open and Pending tickets. Cleared false resolution dates on unresolved tickets to prevent skewing average resolution metrics.
7. **Rejection vs Imputation Policy:** Records missing primary key `ticket_id` or unparseable `created_at` are rejected with entries logged in `DataQualityReport.rejection_log`. Missing optional string fields (`subject`, `description`, `customer_id`) are imputed with traceable audit markers (`"No Subject Provided"`, `"CUST-UNKNOWN"`) and logged in `imputed_fields`.
8. **Idempotent Ingestion & Duplicate Prevention:** Employed `INSERT OR IGNORE` with pre- and post-count delta calculation. Ensures re-importing identical files causes zero duplicate records while tracking skipped rows in `ingestion_logs`.
9. **Query Performance Optimization:** Added composite single-column indexes on `status`, `category`, `created_at`, `priority`, and `is_unresolved` to ensure sub-millisecond analytical aggregations.

---

## 8. Development History
- **2026-10-31:** Initialized `CONTEXT.md` defining project requirements, architecture, roadmaps, and schema. Started Module 1.
- **2026-10-31:** Initialized Git repository and created `.gitignore`, `.env.example`, and `requirements.txt`.
- **2026-10-31:** Created Python 3.13 virtual environment (`.venv`) and installed all core dependencies (`pandas`, `streamlit`, `plotly`, `requests`, `fastapi`, `uvicorn`, `python-dotenv`, `google-genai`, `pytest`). Verified via import check.
- **2026-10-31:** Created comprehensive `data/DATA_DICTIONARY.md` mapping columns to business questions.
- **2026-10-31:** Fixed CSV unquoted-comma parsing error by implementing `scripts/generate_sample_dataset.py` using `csv.writer`; verified clean parsing of 60 rows across 10 attributes via `scripts/inspect_dataset.py`. Module 1 marked **TESTED**.
- **2026-10-31:** Implemented Module 2 (`src/ingestion.py`) with empty-file guards, column aliasing, and non-destructive DataFrame ingestion. Created `tests/test_ingestion.py` with 7 test cases. All 7 tests passed. Module 2 marked **TESTED**.
- **2026-10-31:** Implemented Module 3 (`src/transformation.py`) with duplicate removal, taxonomy standardisation, timestamp parsing, `resolution_time_hours` calculation, and `DataQualityReport`. Created `tests/test_transformation.py` with 9 unit test cases. Total test suite of 16 tests passing in 0.83s. Module 3 marked **TESTED**.
- **2026-10-31:** Implemented Module 4 (`src/database.py`) with SQLite schema, indexes, audit logging, and duplicate prevention via `INSERT OR IGNORE`. Created `tests/test_database.py` with 6 unit test cases. Total test suite of 22 tests passing in 1.23s. Module 4 marked **TESTED**.

---

## 9. Active Error Log
*No active errors.*

---

## 10. Known Limitations and Pending Work
- Data is safely stored in SQLite; the 7 mandatory business SQL analytics queries need to be built in Module 5.

---

## 11. Current State and Exact Next Step
- **Current State:** Modules 1, 2, 3, and 4 completed and verified with 22 passing unit tests.
- **Exact Next Step:** Proceed to **Module 5: SQL Analytics and Business Metrics**:
  1. Build `src/analytics.py` implementing the 7 mandatory business queries.
  2. Implement structured query executor returning both tabular DataFrames and summary KPI dictionaries for dashboard & GenAI consumption.
  3. Write test cases in `tests/test_analytics.py` to verify SQL calculation correctness against known dataset figures.

---

## 12. Instructions for the Next AI Assistant
If resuming or taking over:
- Read `CONTEXT.md` first to confirm current progress and decisions.
- Verify status against actual files in `d:\A Capstone`.
- Follow the Module Roadmap in Section 3. Do not jump ahead without verifying current module tests.
- Always update `CONTEXT.md` after adding or modifying files or fixing issues.
