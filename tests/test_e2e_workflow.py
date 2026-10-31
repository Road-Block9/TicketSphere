"""
End-to-End Application Lifecycle Integration Test
Module 11: Testing and Error Handling - TicketSphere

Executes the full end-to-end data pipeline and user journey on an isolated database:
1. Clean Initial State Verification (empty metrics, zero tickets)
2. CSV Ingestion with Data Quality Audit (valid, invalid, and intra-batch duplicates)
3. Duplicate Prevention on Repeated Ingestion (zero count inflation)
4. SQL Analytics Calculation & Filtered Multi-Dimensional Queries
5. REST API Ticket Ingestion & Unified Database Cohesion
6. Ticket Search, Status Filtering, and Keyword Querying
7. Grounded GenAI Business Report Generation without Hallucinated Metrics
"""

import io
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from src.database import init_db, get_ticket_count
from src.flask_app import app


@pytest.fixture
def isolated_e2e_env(tmp_path):
    """
    Sets up a completely isolated SQLite test database and configures Flask.
    """
    db_path = tmp_path / "ticketsphere_e2e.db"
    init_db(db_path)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, str(db_path)


SAMPLE_E2E_CSV = """ticket_id,created_at,resolved_at,status,category,priority,subject,description,customer_id
TKT-E2E-001,2026-03-01 09:00:00,,Open,Technical Support,High,App crash on checkout,User cannot pay,CUST-101
TKT-E2E-002,2026-03-01 10:00:00,2026-03-01 14:00:00,Closed,Billing & Refunds,Medium,Refund request,Refund processed promptly,CUST-102
TKT-E2E-003,2026-03-01 11:00:00,,Pending,Delivery & Shipping,Critical,Missing package,Courier package lost,CUST-103
TKT-E2E-004,2026-03-01 12:00:00,2026-03-01 16:30:00,Resolved,Technical Support,Low,Password reset,Self service link sent,CUST-104
,2026-03-01 13:00:00,,Open,Billing & Refunds,Low,Invalid missing ID,Should be rejected,CUST-105
TKT-E2E-001,2026-03-01 09:00:00,,Open,Technical Support,High,Duplicate ID within file,Duplicate should be skipped,CUST-101
"""


def test_e2e_complete_application_lifecycle(isolated_e2e_env):
    """
    Simulates a full user session across all system layers using an isolated database.
    """
    client, db_path = isolated_e2e_env

    with patch("src.database.get_db_path", return_value=db_path):
        # -----------------------------------------------------------------
        # Step 1: Verify Initial Clean State
        # -----------------------------------------------------------------
        health_resp = client.get("/api/health")
        assert health_resp.status_code == 200
        assert health_resp.get_json()["status"] == "healthy"
        assert health_resp.get_json()["total_tickets_in_db"] == 0

        kpis_resp = client.get("/api/analytics/kpis")
        assert kpis_resp.status_code == 200
        kpis_data = kpis_resp.get_json()["data"]
        assert kpis_data["total_tickets"] == 0
        assert kpis_data["open_tickets"] == 0
        assert kpis_data["unresolved_tickets"] == 0
        assert kpis_data["avg_resolution_hours"] == 0.0

        tickets_resp = client.get("/api/tickets")
        assert tickets_resp.status_code == 200
        assert tickets_resp.get_json()["count"] == 0

        # -----------------------------------------------------------------
        # Step 2: Upload CSV with mixed data quality
        # -----------------------------------------------------------------
        csv_file = io.BytesIO(SAMPLE_E2E_CSV.encode("utf-8"))
        upload_resp = client.post(
            "/api/ingest/csv",
            data={"file": (csv_file, "sample_support_data.csv")},
            content_type="multipart/form-data"
        )
        assert upload_resp.status_code == 200
        upload_json = upload_resp.get_json()
        assert upload_json["status"] == "success"
        assert upload_json["database"]["records_inserted"] == 4
        assert upload_json["database"]["records_skipped_duplicate"] == 0

        # Verify Data Quality breakdown
        dq = upload_json["data_quality"]
        assert dq["total_received"] == 6
        assert dq["accepted"] == 4
        assert dq["rejected"] == 1  # missing ticket_id
        assert dq["duplicates_dropped"] == 1  # duplicate TKT-E2E-001 within file

        # Verify Database record count
        assert get_ticket_count(db_path) == 4

        # -----------------------------------------------------------------
        # Step 3: Duplicate Prevention on Repeated Ingestion
        # -----------------------------------------------------------------
        csv_file_repeat = io.BytesIO(SAMPLE_E2E_CSV.encode("utf-8"))
        repeat_resp = client.post(
            "/api/ingest/csv",
            data={"file": (csv_file_repeat, "sample_support_data.csv")},
            content_type="multipart/form-data"
        )
        assert repeat_resp.status_code == 200
        repeat_json = repeat_resp.get_json()
        assert repeat_json["status"] == "success"
        assert repeat_json["database"]["records_inserted"] == 0
        assert repeat_json["database"]["records_skipped_duplicate"] == 4  # All 4 previously stored tickets skipped

        # Record count in database must remain exactly 4
        assert get_ticket_count(db_path) == 4

        # -----------------------------------------------------------------
        # Step 4: SQL Analytics Calculation & Filtered Queries
        # -----------------------------------------------------------------
        kpis_after = client.get("/api/analytics/kpis").get_json()["data"]
        assert kpis_after["total_tickets"] == 4
        assert kpis_after["open_tickets"] == 1  # TKT-E2E-001
        assert kpis_after["unresolved_tickets"] == 2  # Open (TKT-E2E-001) + Pending (TKT-E2E-003)

        # Average resolution time:
        # TKT-E2E-002: 10:00 to 14:00 = 4.0 hours
        # TKT-E2E-004: 12:00 to 16:30 = 4.5 hours
        # Average: (4.0 + 4.5) / 2 = 4.25 hours
        assert kpis_after["avg_resolution_hours"] == 4.25

        # Category filter test
        filtered_resp = client.get("/api/analytics/kpis?category=Technical+Support")
        assert filtered_resp.status_code == 200
        cat_kpis = filtered_resp.get_json()["data"]
        assert cat_kpis["total_tickets"] == 2
        assert cat_kpis["open_tickets"] == 1

        # Priority filter test
        crit_resp = client.get("/api/analytics/kpis?priority=Critical")
        assert crit_resp.status_code == 200
        crit_kpis = crit_resp.get_json()["data"]
        assert crit_kpis["total_tickets"] == 1
        assert crit_kpis["unresolved_tickets"] == 1

        # -----------------------------------------------------------------
        # Step 5: Ingest API Records into Unified Database
        # -----------------------------------------------------------------
        api_tickets = [
            {
                "ticket_id": "TKT-API-201",
                "created_at": "2026-03-02 08:00:00",
                "resolved_at": None,
                "status": "Open",
                "category": "Billing & Refunds",
                "priority": "High",
                "subject": "Double charged on subscription",
                "description": "Card was billed twice for annual plan.",
                "customer_id": "CUST-201"
            },
            {
                "ticket_id": "TKT-API-202",
                "created_at": "2026-03-02 09:30:00",
                "resolved_at": "2026-03-02 11:30:00",
                "status": "Resolved",
                "category": "Account & Login",
                "priority": "Medium",
                "subject": "Two factor auth reset",
                "description": "User switched devices and lost authenticator.",
                "customer_id": "CUST-202"
            }
        ]

        mock_fetch_result = MagicMock()
        mock_fetch_result.success = True
        mock_fetch_result.data = pd.DataFrame(api_tickets)
        mock_fetch_result.record_count = 2
        mock_fetch_result.source_type = "SIMULATED_MOCK_API"
        mock_fetch_result.error_message = None

        with patch("src.api_client.fetch_tickets_from_api", return_value=mock_fetch_result):
            api_resp = client.post("/api/ingest/api", json={"api_url": "http://127.0.0.1:8000/api/v1/tickets"})
            assert api_resp.status_code == 200
            api_json = api_resp.get_json()
            assert api_json["status"] == "success"
            assert api_json["database"]["records_inserted"] == 2
            assert api_json["database"]["records_skipped_duplicate"] == 0

            # Verify unified database total: 4 (from CSV) + 2 (from API) = 6 tickets
            assert get_ticket_count(db_path) == 6

        # -----------------------------------------------------------------
        # Step 6: Ticket Search and Filtering Endpoints
        # -----------------------------------------------------------------
        # Search by keyword
        search_resp = client.get("/api/tickets?search=checkout")
        assert search_resp.status_code == 200
        search_data = search_resp.get_json()
        assert search_data["count"] == 1
        assert search_data["tickets"][0]["ticket_id"] == "TKT-E2E-001"

        # Filter by status: open (should be 2 open: TKT-E2E-001 and TKT-API-201)
        open_resp = client.get("/api/tickets?status=Open")
        assert open_resp.status_code == 200
        open_data = open_resp.get_json()
        assert open_data["count"] == 2

        # -----------------------------------------------------------------
        # Step 7: Grounded GenAI Business Report
        # -----------------------------------------------------------------
        with patch.dict("os.environ", {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
            report_resp = client.post("/api/ai/report")
            assert report_resp.status_code == 200
            report_json = report_resp.get_json()
            assert report_json["status"] == "success"
            assert report_json["is_fallback"] is True

            # Verify content uses verified metrics (6 total tickets) without fabrication
            content = report_json["report"]
            assert "6 customer tickets" in content
            assert "Technical Support" in content or "Billing & Refunds" in content
