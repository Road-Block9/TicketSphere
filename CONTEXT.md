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
| **Module 5** | SQL Analytics Queries | 7 business SQL queries, verification tests | **TESTED** |
| **Module 6** | API Data Ingestion | Mock REST API (FastAPI) & HTTP client (requests), timeout/auth handling | **TESTED** |
| **Module 7** | GenAI Business Assistant | Grounded prompt engineer, LLM integration & fallback reporter | **TESTED** |
| **Module 8** | React Frontend & Flask API | Modern React + Tailwind dashboard, Flask backend API, theme toggle | **TESTED** |
| **Module 9** | Dashboard Analytics & Visualisation | Recharts bar/donut/area charts, unresolved hotspots table, interactive date/category/priority filters | **TESTED** |
| **Module 10** | Integrate the Complete Pipeline | Coordinated orchestration (src/pipeline.py), duplicate prevention, cross-module workflow in TicketSphere | **TESTED** |
| **Module 11** | Testing and Error Handling | Comprehensive unit tests, error handling suite, E2E integration test, 78 pytest tests passing | **TESTED** |

---

## 4. Environment and Setup
- **Operating System:** Windows 10/11
- **Python Version:** 3.13.3
- **Node.js Version:** 22.23.0 (npm 11.17.0)
- **Git Version:** 2.54.0.windows.1
- **Working Directory:** `d:\A Capstone`
- **Virtual Environment:** `.venv` (created via `python -m venv .venv`, all dependencies installed and verified)
- **Backend Server:** Flask REST API on `http://127.0.0.1:5000`
- **Frontend Server:** Vite + React + Tailwind CSS on `http://127.0.0.1:5173` (TicketSphere)

---

## 5. Dataset and Data Schema
### Target Unified Schema (`tickets`)
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `ticket_id` | TEXT / PRIMARY KEY | Unique ticket identifier (e.g., TKT-1001, TKT-API-2001) |
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
- `.gitignore`: Configured to exclude `.venv/`, `__pycache__/`, `*.db`, `.env`, `.pytest_cache/`, `frontend/node_modules/`, `frontend/dist/`.
- `.env.example`: Configuration template for API keys, DB path, Flask port, and mock API host/port.
- `requirements.txt`: Pinned dependencies for Pandas, Requests, FastAPI, Uvicorn, Flask, Flask-CORS, python-dotenv, google-genai, pytest.
- `data/DATA_DICTIONARY.md`: Complete column specifications, integrity rules, and mapping to 7 business questions.
- `data/raw/customer_support_tickets.csv`: 60 realistic ticket records with valid timestamps, categories, and resolution notes.
- `data/processed/customer_support.db`: Persistent SQLite database initialized with `tickets` and `ingestion_logs` tables.
- `scripts/generate_sample_dataset.py`: Generator script ensuring correct CSV standard escaping and quote wrapping.
- `scripts/inspect_dataset.py`: Verified dataset auditing script reporting shape, nulls, and distributions.
- `src/__init__.py`: Application source package marker.
- `src/ingestion.py`: Robust CSV reader and validator supporting file paths and uploaded buffers, column alias normalization, and error auditing.
- `src/transformation.py`: Comprehensive cleaning engine with duplicate removal, taxonomy standardisation, timestamp parsing, `resolution_time_hours` calculation, and a structured `DataQualityReport`.
- `src/database.py`: Database management module with SQLite schema initialization, transactional idempotent loader (`INSERT OR IGNORE`), duplicate prevention, and parameterised SQL query executor.
- `src/analytics.py`: SQL analytics engine implementing the 7 mandatory business queries, aggregated KPI dictionary, structured grounding digest for GenAI, and parameterised filtering by reporting period (`start_date`/`end_date`), `category`, and `priority`.
- `src/mock_api.py`: Local FastAPI REST service simulating an enterprise support API with Swagger docs (`/docs`), health check (`/health`), query params, and API key authentication.
- `src/api_client.py`: Production-grade HTTP API client with timeout protection, auth headers, and unified pipeline connector (`ingest_api_pipeline`).
- `src/genai_assistant.py`: AI Support Insights Assistant integrating Google Gemini API via official SDK, strictly grounded prompt engineering, and an honest deterministic fallback reporter.
- `src/pipeline.py`: Centralized pipeline orchestrator coordinating ingestion validation, cleaning/transformation, idempotent database storage, and analytics refresh (`run_csv_pipeline`, `run_api_pipeline`, `run_full_pipeline_cycle`).
- `src/flask_app.py`: Flask REST API backend exposing `/api/health`, `/api/analytics/kpis` (with query filtering), `/api/tickets`, `/api/ingest/csv`, `/api/ingest/api`, `/api/ai/report` with CORS enabled.
- `frontend/package.json`: React 19 + Vite project with Tailwind CSS v3.4.17, Recharts v2.15.1, PostCSS, Autoprefixer, and Lucide React icons.
- `frontend/tailwind.config.js`: Tailwind configuration supporting class-based dark mode (`darkMode: 'class'`) and Google Inter/JetBrains Mono fonts.
- `frontend/src/api.js`: Central frontend API client connecting to Flask endpoints with error handling, query param serialization, and environment variable support (`VITE_API_URL`).
- `frontend/src/components/Sidebar.jsx`: TicketSphere brand navigation sidebar with module links and live Flask connectivity status badge.
- `frontend/src/components/Header.jsx`: Top navigation header with module titles, breadcrumbs, live data refresh button, and light/dark theme switch.
- `frontend/src/components/OverviewTab.jsx`: Comprehensive analytics view featuring 5 KPI cards, interactive date/category/priority filter toolbar, Recharts bar chart of complaint categories, Recharts status donut chart, Recharts volume timeline area chart, and unresolved hotspots table.
- `frontend/src/components/IngestionTab.jsx`: Dual-pipeline ingestion dashboard for CSV drag-and-drop file upload and REST API trigger with live Data Quality audit breakdown and quick navigation buttons.
- `frontend/src/components/GenAITab.jsx`: GenAI executive management report generator with loading spinner, runtime stats, model badge, grounding disclaimer banner, and copy-to-clipboard functionality.
- `frontend/src/components/TicketsTab.jsx`: Ticket explorer with live search, status/category/priority filter dropdowns, count badge, responsive data table, expandable ticket details, and auto-refresh integration on new ingestions.
- `frontend/src/App.jsx`: Main TicketSphere application shell with theme persistence in `localStorage`, active tab routing, and central data synchronization.
- `tests/__init__.py`: Test suite package marker.
- `tests/test_ingestion.py`: 7 automated pytest test cases covering file reading, validation, empty files, and buffer streams.
- `tests/test_transformation.py`: 9 automated pytest test cases covering deduplication, taxonomy mapping, duration math, and anomaly clearance.
- `tests/test_database.py`: 6 automated pytest test cases covering schema creation, duplicate prevention on repeated imports, data retrieval, and parameterised queries.
- `tests/test_analytics.py`: 10 automated pytest test cases covering all 7 business SQL queries, empty-database resilience, and parameterised filtering by date, category, and priority.
- `tests/test_api_ingestion.py`: 9 automated pytest test cases covering FastAPI endpoints, auth, status filtering, connection errors, timeouts, and end-to-end pipeline execution.
- `tests/test_genai.py`: 5 automated pytest test cases covering grounded prompts, deterministic fallback, empty data handling, simulated API calls, and exception fallback.
- `tests/test_flask_api.py`: 7 automated pytest test cases validating Flask REST API endpoints (`/api/health`, `/api/analytics/kpis` with filters, `/api/tickets`, `/api/ingest/csv`, `/api/ingest/api`, `/api/ai/report`).
- `tests/test_pipeline.py`: 6 automated pytest test cases validating end-to-end pipeline orchestration, duplicate prevention during repeated imports, empty file handling, missing column validation, full cycle execution with GenAI report generation, and API error resilience. (59 total passing unit tests across repository).

---

## 7. Design Decisions and Their Reasons
1. **SQLite over complex DB engines:** Zero-setup, single-file relational database ideal for capstone review, reproducible across reviewer machines without installing PostgreSQL/MySQL services.
2. **Deterministic Fallback for GenAI:** In corporate reviews or offline demos where an external API key is invalid or rate-limited, the system seamlessly falls back to a template-driven analytical report without crashing or fabricating fake AI output.
3. **Local REST API Mock:** Zendesk and enterprise tools require paid accounts or business credit cards; a lightweight local mock server provides a real HTTP request/response pipeline matching the capstone requirement at zero cost.
4. **CSV Quoting Protocol:** Used Python `csv.writer` with `QUOTE_MINIMAL` to prevent commas inside ticket descriptions from breaking Pandas CSV tokenization.
5. **Polymorphic Ingestion Target (`str`, `Path`, `BytesIO`, `StringIO`):** Designed `read_csv_tickets` in `src/ingestion.py` to ingest from both filesystem paths and uploaded stream buffers, guaranteeing identical validation in the CLI, Flask API, and the React UI.
6. **No Fabricated Resolution Times:** Strictly set `resolution_time_hours` and `resolved_at` to `None`/`NaN` for Open and Pending tickets. Cleared false resolution dates on unresolved tickets to prevent skewing average resolution metrics.
7. **Rejection vs Imputation Policy:** Records missing primary key `ticket_id` or unparseable `created_at` are rejected with entries logged in `DataQualityReport.rejection_log`. Missing optional string fields (`subject`, `description`, `customer_id`) are imputed with traceable audit markers (`"No Subject Provided"`, `"CUST-UNKNOWN"`) and logged in `imputed_fields`.
8. **Idempotent Ingestion & Duplicate Prevention:** Employed `INSERT OR IGNORE` with pre- and post-count delta calculation. Ensures re-importing identical files causes zero duplicate records while tracking skipped rows in `ingestion_logs`.
9. **Query Performance Optimization:** Added composite single-column indexes on `status`, `category`, `created_at`, `priority`, and `is_unresolved` to ensure sub-millisecond analytical aggregations.
10. **Dual-Format Analytics API:** `src/analytics.py` functions return raw Pandas DataFrames for chart visualisations AND pre-formatted text digests (`format_analytics_summary_text`) to ground the GenAI model strictly in verified facts.
11. **Unified Pipeline Architecture:** Both CSV ingestion (`src/ingestion.py`) and API ingestion (`src/api_client.py`) flow through the exact same transformation engine (`src/transformation.py`) and SQLite storage loader (`src/database.py`), preventing code duplication and guaranteeing identical quality standards across channels.
12. **Anti-Hallucination Grounding & Free-Tier SDK:** Utilized Google's latest `google-genai` SDK targeting `gemini-2.5-flash` (zero cost free tier) with strict grounding constraints. Provided an honest fallback report clearly labeled whenever external keys are omitted.
13. **Separate Frontend & Backend Architecture:** React + Vite in `frontend/` and Flask in `src/flask_app.py` ensure clear separation of concerns. Flask acts purely as an API gateway that invokes Modules 1 to 7 without duplicating any business or data pipeline logic.
14. **Persistent Dark/Light Mode:** Controlled via Tailwind `class` on `<html className="dark">` and synchronized with `localStorage.theme`, respecting system theme on initial visit.
15. **Configurable API Client:** `frontend/src/api.js` defaults to `http://127.0.0.1:5000` but dynamically reads `VITE_API_URL` from Vite's environment variables for zero-code configuration during deployment.
16. **Dynamic Parameterised SQL Analytics Filtering:** Implemented `_build_filter_clause` in `src/analytics.py` to enable filtering by reporting period (`start_date`/`end_date`), `category`, and `priority` using secure parameterised SQL queries, avoiding client-side recalculation and ensuring charts reflect database ground truth.
17. **Theme-Adaptive Recharts Components:** Recharts grid strokes, axes text colors, tooltips, and legends are linked directly to the application's active light/dark theme to maintain contrast and readable typography across themes.
18. **Pipeline Orchestration Decoupling:** Implemented `src/pipeline.py` to coordinate the full multi-stage workflow (ingestion -> validation -> transformation -> idempotent storage -> analytics snapshot). Decouples business logic from Flask request/response wrappers, enabling clean unit testing and end-to-end cycle verification.

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
- **2026-10-31:** Implemented Module 5 (`src/analytics.py`) answering the 7 core business questions, KPI aggregation, and GenAI grounding formatter. Created `tests/test_analytics.py` with 8 unit test cases. Total test suite of 30 tests passing in 1.77s. Module 5 marked **TESTED**.
- **2026-10-31:** Implemented Module 6 (`src/mock_api.py` and `src/api_client.py`) adding documented mock REST API with Swagger UI and HTTP client with error/timeout handling. Connected API ingestion end-to-end to transformation and SQLite loader. Created `tests/test_api_ingestion.py` with 9 unit test cases. Total test suite of 39 tests passing in 2.45s. Module 6 marked **TESTED**.
- **2026-10-31:** Implemented Module 7 (`src/genai_assistant.py`) integrating Gemini API with grounded prompt engineering and an honest deterministic fallback reporter. Fixed Windows cp1252 terminal UnicodeEncodeError by configuring utf-8 stdout; verified via standalone execution. Created `tests/test_genai.py` with 5 unit test cases. Total test suite of 44 tests passing in 2.95s. Module 7 marked **TESTED**.
- **2026-10-31:** Implemented Module 8 (`src/flask_app.py` & `frontend/` React + Vite + Tailwind CSS dashboard). Added `flask` and `flask-cors` to requirements. Built REST endpoints connecting to existing Modules 1 to 7 without duplicating logic. Created `tests/test_flask_api.py` with 6 automated tests. Built React components (`Sidebar`, `Header`, `OverviewTab`, `IngestionTab`, `GenAITab`, `TicketsTab`), centralized API client (`api.js`), and dark mode theme toggle with `localStorage` persistence. Verified `npm run build` passes with zero errors, and verified live HTTP responses on `http://127.0.0.1:5000` and `http://127.0.0.1:5173`. Module 8 marked **TESTED**.
- **2026-10-31:** Implemented Module 9 (Dashboard Analytics and Visualisation). Installed `recharts`. Updated `src/analytics.py` with `_build_filter_clause` supporting parameterised filtering by `start_date`, `end_date`, `category`, and `priority` across all queries. Extended `/api/analytics/kpis` in `src/flask_app.py` to parse query parameters. Updated `frontend/src/api.js` to serialize filter options. Built complete visual analytics dashboard in `frontend/src/components/OverviewTab.jsx` with KPI cards, Recharts complaint categories bar chart, Recharts status donut chart, Recharts volume timeline area chart, and unresolved hotspots table, fully integrated with light and dark themes. Added automated tests in `tests/test_analytics.py` and `tests/test_flask_api.py` (53/53 tests passing). Verified production build and live filtered API responses. Module 9 marked **TESTED**.
- **2026-10-31:** Implemented Module 10 (Integrate the Complete Pipeline). Created `src/pipeline.py` unifying CSV ingestion, API ingestion, data cleaning & quality audit, idempotent database storage, and post-ingestion analytics refresh into cohesive workflows (`run_csv_pipeline`, `run_api_pipeline`, `run_full_pipeline_cycle`). Connected Flask routes `/api/ingest/csv` and `/api/ingest/api` to orchestrator. Updated TicketSphere branding across `Sidebar.jsx`, `index.html`. Connected `TicketsTab` auto-refresh on new ingestion and added quick workflow action buttons in `IngestionTab`. Created `tests/test_pipeline.py` (6 unit tests, total 59/59 passing tests across repository). Verified live HTTP duplicate prevention (60 skipped duplicates on repeated import) and fresh grounded AI executive reports. Module 10 marked **TESTED**.
- **2026-10-31:** Implemented Module 11 (Testing and Error Handling). Created `tests/test_error_handling.py` (18 tests) covering malformed/empty CSVs, corrupted timestamps, rejected missing primary keys, SQL injection resilience, external API timeouts/connection errors/HTTP 500s, empty API datasets, GenAI credential absence/quota exhaustion deterministic fallback, and Flask 400 error handling. Created `tests/test_e2e_workflow.py` (1 end-to-end integration test) simulating complete multi-step user lifecycle on an isolated database (clean state -> CSV ingestion -> DQ verification -> duplicate prevention on repeated import -> SQL analytics verification -> API ingestion -> search/filtering -> grounded GenAI report). Discovered and fixed `KeyError: 'total_in_db'` in `src/pipeline.py` during API pipeline run. Cleaned up unused React component imports, verified `npm run build` and `oxlint` with 0 errors. Total test suite across 10 test files is **78/78 passing in 8.45s**. Module 11 marked **TESTED**.
- **2026-10-31:** Completed KPI Card Color Styling Update in `frontend/src/components/OverviewTab.jsx`. Applied reference pastel palette in light mode: Card 1 (`#D6EBFF` soft sky blue), Card 2 (`#EBD5FF` soft lavender), Card 3 (`#FFF0BF` pale warm yellow), Card 4 (`#FFE0D2` soft peach), and Card 5 cycling back to `#D6EBFF`. Configured dark mode styling using restrained charcoal surfaces (`#131b26`, `#1a1528`, `#201c14`, `#221714`) with subtle colored borders and complementary icon badges. Maintained WCAG AAA contrast with dark text (`text-slate-900`/`text-slate-700`) on light pastel backgrounds and `dark:text-white`/`dark:text-slate-300` on dark surfaces. Verified zero regressions via `npm run build` (1.29s) and full Pytest suite (78/78 passing).

---

## 9. Active Error Log
*No active errors.*

---

## 10. Known Limitations and Pending Work
- Automated browser testing using Playwright driver encountered sandbox network download restrictions (offline 404); application frontend verified via Vite production build, linter, and live HTTP dev servers (`http://127.0.0.1:5173` and `http://127.0.0.1:5000`).
- Documentation (`README.md`), presentation outline, and final capstone packaging are ready to be completed.

---

## 11. Current State and Exact Next Step
- **Current State:** All core modules (1 to 11) and the KPI Card Color Styling update are completed, verified, and passing 78 automated Pytest tests, with zero linter errors and zero build errors.
- **Exact Next Step:** Proceed to Module 12 wrap-up documentation:
  1. Write comprehensive `README.md` with system architecture diagrams, tech stack breakdown, setup instructions, and capstone requirements mapping.
  2. Finalize presentation outline and evaluation talking points.

---

## 12. Instructions for the Next AI Assistant
If resuming or taking over:
- Read `CONTEXT.md` first to confirm current progress and decisions.
- Verify status against actual files in `d:\A Capstone`.
- Follow the Module Roadmap in Section 3. Do not jump ahead without verifying current module tests.
- Always update `CONTEXT.md` after adding or modifying files or fixing issues.
