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
| **Module 2** | Data Ingestion (File & API) | CSV ingestion module, documented local/mock API client & endpoint | NOT STARTED |
| **Module 3** | Data Transformation & Quality | Pandas cleaning, deduplication, resolution metrics, DQ report | NOT STARTED |
| **Module 4** | Relational Database & Storage | SQLite schema, idempotent loader, duplicate prevention | NOT STARTED |
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

---

## 6. Implemented Features and Important Files
- `CONTEXT.md`: Permanent continuity and state tracker.
- `.gitignore`: Configured to exclude `.venv/`, `__pycache__/`, `*.db`, `.env`, `.pytest_cache/`.
- `.env.example`: Configuration template for API keys, DB path, and mock API host/port.
- `requirements.txt`: Pinned dependencies for Pandas, Streamlit, Plotly, Requests, FastAPI, Uvicorn, pytest, google-genai.
- `data/DATA_DICTIONARY.md`: Complete column specifications, integrity rules, and mapping to 7 business questions.
- `data/raw/customer_support_tickets.csv`: 60 realistic ticket records with valid timestamps, categories, and resolution notes.
- `scripts/generate_sample_dataset.py`: Generator script ensuring correct CSV standard escaping and quote wrapping.
- `scripts/inspect_dataset.py`: Verified dataset auditing script reporting shape, nulls, and distributions.
- `src/__init__.py`: Application source package marker.
- `tests/__init__.py`: Test suite package marker.

---

## 7. Design Decisions and Their Reasons
1. **SQLite over complex DB engines:** Zero-setup, single-file relational database ideal for capstone review, reproducible across reviewer machines without installing PostgreSQL/MySQL services.
2. **Deterministic Fallback for GenAI:** In corporate reviews or offline demos where an external API key is invalid or rate-limited, the system seamlessly falls back to a template-driven analytical report without crashing or fabricating fake AI output.
3. **Local REST API Mock:** Zendesk and enterprise tools require paid accounts or business credit cards; a lightweight local mock server provides a real HTTP request/response pipeline matching the capstone requirement at zero cost.
4. **CSV Quoting Protocol:** Used Python `csv.writer` with `QUOTE_MINIMAL` to prevent commas inside ticket descriptions from breaking Pandas CSV tokenization.

---

## 8. Development History
- **2026-10-31:** Initialized `CONTEXT.md` defining project requirements, architecture, roadmaps, and schema. Started Module 1.
- **2026-10-31:** Initialized Git repository and created `.gitignore`, `.env.example`, and `requirements.txt`.
- **2026-10-31:** Created Python 3.13 virtual environment (`.venv`) and installed all core dependencies (`pandas`, `streamlit`, `plotly`, `requests`, `fastapi`, `uvicorn`, `python-dotenv`, `google-genai`, `pytest`). Verified via import check.
- **2026-10-31:** Created comprehensive `data/DATA_DICTIONARY.md` mapping columns to business questions.
- **2026-10-31:** Fixed CSV unquoted-comma parsing error by implementing `scripts/generate_sample_dataset.py` using `csv.writer`; verified clean parsing of 60 rows across 10 attributes via `scripts/inspect_dataset.py`. Module 1 marked **TESTED**.

---

## 9. Active Error Log
*No active errors.*

---

## 10. Known Limitations and Pending Work
- Raw data currently exists as a flat file; ingestion pipeline (CSV upload + API endpoint) needs to be built in Module 2.

---

## 11. Current State and Exact Next Step
- **Current State:** Module 1 completed and verified. Virtual environment ready, dataset generated and audited, inspection script tested.
- **Exact Next Step:** Proceed to **Module 2: Data Ingestion (File and API)**:
  1. Build `src/ingestion.py` supporting both CSV file reading with validation (empty file checks, malformed row handling).
  2. Implement a local FastAPI mock support ticket endpoint (`src/mock_api.py`) simulating an external API (e.g., Zendesk-like JSON response).
  3. Implement API ingestion in `src/ingestion.py` to fetch tickets over HTTP via `requests`.
  4. Write test script to verify both ingestion routes.

---

## 12. Instructions for the Next AI Assistant
If resuming or taking over:
- Read `CONTEXT.md` first to confirm current progress and decisions.
- Verify status against actual files in `d:\A Capstone`.
- Follow the Module Roadmap in Section 3. Do not jump ahead without verifying current module tests.
- Always update `CONTEXT.md` after adding or modifying files or fixing issues.
