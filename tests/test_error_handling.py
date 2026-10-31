"""
Comprehensive Error Handling & Edge Case Tests
Module 11: Testing and Error Handling - TicketSphere

Tests safety, graceful failure recovery, and resilience across:
1. Ingestion of malformed, empty, and corrupted CSV files
2. External API failure simulation (timeouts, HTTP 500s, invalid JSON)
3. Database error recovery and parameterised SQL injection resilience
4. GenAI missing credentials, rate limit exceptions, and deterministic fallback
5. Flask REST API error handling and status code validation
"""

import io
import pytest
from unittest.mock import patch, MagicMock
import requests
import pandas as pd
from pathlib import Path

from src.ingestion import read_csv_tickets
from src.transformation import clean_and_transform_tickets
from src.database import init_db, insert_tickets, get_ticket_count, execute_query
from src.analytics import get_all_analytics_kpis
from src.api_client import fetch_tickets_from_api, ingest_api_pipeline
from src.genai_assistant import generate_support_insights_report
from src.flask_app import app


@pytest.fixture
def isolated_db(tmp_path):
    """Provides an isolated SQLite database."""
    db_file = tmp_path / "error_test.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def client():
    """Provides Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# =====================================================================
# 1. CSV INGESTION & TRANSFORMATION ERROR HANDLING
# =====================================================================

def test_ingestion_empty_file():
    """Verifies that an empty CSV stream produces an explicit error without crashing."""
    res = read_csv_tickets(io.StringIO(""))
    assert res.success is False
    assert res.record_count == 0
    assert any("empty" in err.lower() for err in res.errors)


def test_ingestion_header_only_file():
    """Verifies that a CSV file with only headers and no rows is caught."""
    header_only = "ticket_id,created_at,status,category,priority,subject,description\n"
    res = read_csv_tickets(io.StringIO(header_only))
    assert res.success is False
    assert res.record_count == 0
    assert any("empty" in err.lower() or "0" in err or "zero" in err.lower() for err in res.errors)


def test_ingestion_missing_required_columns():
    """Verifies missing required columns are flagged with specific missing column names."""
    bad_csv = "subject,description\nIssue title,Issue description\n"
    res = read_csv_tickets(io.StringIO(bad_csv))
    assert res.success is False
    assert any("ticket_id" in err.lower() for err in res.errors)
    assert any("status" in err.lower() for err in res.errors)


def test_transformation_all_rejected_rows():
    """Verifies behavior when all rows in a DataFrame have invalid primary keys."""
    raw_df = pd.DataFrame([
        {"ticket_id": None, "created_at": "2026-03-01 10:00:00", "status": "Open", "category": "Technical Support"},
        {"ticket_id": "", "created_at": "2026-03-01 11:00:00", "status": "Open", "category": "Billing & Refunds"},
    ])
    cleaned_df, dq = clean_and_transform_tickets(raw_df)
    assert len(cleaned_df) == 0
    assert dq.rejected == 2
    assert dq.accepted == 0


def test_transformation_corrupted_timestamps():
    """Verifies that completely non-date strings in created_at are rejected safely."""
    raw_df = pd.DataFrame([
        {"ticket_id": "TKT-ERR-1", "created_at": "not-a-valid-timestamp-at-all", "status": "Open", "category": "Delivery & Shipping"}
    ])
    cleaned_df, dq = clean_and_transform_tickets(raw_df)
    assert len(cleaned_df) == 0
    assert dq.rejected == 1
    assert any("timestamp" in log["reason"].lower() for log in dq.rejection_log)


# =====================================================================
# 2. DATABASE & SQL INJECTION RESILIENCE
# =====================================================================

def test_database_sql_injection_resilience(isolated_db):
    """Verifies that parameterised query execution neutralizes malicious SQL injection inputs."""
    sample_df = pd.DataFrame([
        {
            "ticket_id": "TKT-SQL-1",
            "created_at": "2026-03-01 10:00:00",
            "status": "Open",
            "category": "Technical Support",
            "priority": "High",
            "subject": "SQL Test",
            "description": "Safe text",
            "is_unresolved": 1
        }
    ])
    insert_tickets(sample_df, db_path=isolated_db)

    # Malicious injection attempt in parameter
    malicious_param = "'; DROP TABLE tickets; --"
    kpis = get_all_analytics_kpis(db_path=isolated_db, category=malicious_param)
    
    # Verify table was NOT dropped and query executed safely
    assert kpis["total_tickets"] == 0  # No category matches the malicious string
    assert get_ticket_count(isolated_db) == 1  # Table and data remain intact


def test_database_insert_empty_dataframe(isolated_db):
    """Verifies that inserting an empty DataFrame returns (0, 0) without database errors."""
    empty_df = pd.DataFrame()
    inserted, skipped = insert_tickets(empty_df, db_path=isolated_db)
    assert inserted == 0
    assert skipped == 0
    assert get_ticket_count(isolated_db) == 0


# =====================================================================
# 3. EXTERNAL API SIMULATION & TIMEOUT HANDLING
# =====================================================================

def test_api_client_timeout_handling():
    """Verifies that requests.Timeout is caught gracefully with structured error."""
    with patch("src.api_client.requests.get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        res = fetch_tickets_from_api("http://127.0.0.1:8000/api/v1/tickets", timeout=1)
        assert res.success is False
        assert "timed out" in res.error_message.lower() or "timeout" in res.error_message.lower()


def test_api_client_connection_error():
    """Verifies that requests.ConnectionError produces clear error information."""
    with patch("src.api_client.requests.get", side_effect=requests.exceptions.ConnectionError("Connection refused")):
        res = fetch_tickets_from_api("http://127.0.0.1:9999/api/v1/tickets")
        assert res.success is False
        assert "connect" in res.error_message.lower()


def test_api_client_http_500_response():
    """Verifies that HTTP 500 server error produces an explicit status error message."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("src.api_client.requests.get", return_value=mock_response):
        res = fetch_tickets_from_api("http://127.0.0.1:8000/api/v1/tickets")
        assert res.success is False
        assert res.status_code == 500
        assert "500" in res.error_message


def test_api_pipeline_empty_ticket_list(isolated_db):
    """Verifies that an API returning an empty ticket list handles smoothly."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.data = pd.DataFrame(columns=["ticket_id", "created_at", "status", "category", "priority", "subject", "description"])
    mock_result.record_count = 0
    mock_result.source_type = "SIMULATED_MOCK_API"

    with patch("src.api_client.fetch_tickets_from_api", return_value=mock_result):
        res = ingest_api_pipeline(db_path=isolated_db)
        assert res["success"] is True
        assert res["inserted_count"] == 0
        assert res["skipped_count"] == 0


# =====================================================================
# 4. GENAI ERROR RECOVERY & FALLBACK HONESTY
# =====================================================================

def test_genai_empty_database_fallback(isolated_db):
    """Verifies that an empty database triggers an honest informative response without hallucinating."""
    report_res = generate_support_insights_report(db_path=isolated_db)
    assert report_res.is_fallback is True
    assert "No customer support ticket records" in report_res.content


def test_genai_missing_key_deterministic_fallback(isolated_db):
    """Verifies that missing GEMINI_API_KEY activates deterministic fallback grounded in metrics."""
    # Seed 1 ticket with full schema
    sample_df = pd.DataFrame([{
        "ticket_id": "TKT-AI-ERR-1",
        "created_at": "2026-03-01 10:00:00",
        "status": "Open",
        "category": "Technical Support",
        "priority": "High",
        "subject": "App freeze",
        "description": "App froze during payment flow.",
        "is_unresolved": 1
    }])
    insert_tickets(sample_df, db_path=isolated_db)

    with patch.dict("os.environ", {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
        report_res = generate_support_insights_report(db_path=isolated_db)
        assert report_res.is_fallback is True
        assert report_res.model_name == "Deterministic Analytical Template Engine"
        assert "1 customer tickets" in report_res.content
        assert "Technical Support" in report_res.content


def test_genai_api_exception_fallback(isolated_db):
    """Verifies that an API exception during GenAI execution falls back gracefully."""
    sample_df = pd.DataFrame([{
        "ticket_id": "TKT-AI-ERR-2",
        "created_at": "2026-03-01 10:00:00",
        "status": "Open",
        "category": "Delivery & Shipping",
        "priority": "Critical",
        "subject": "Lost box",
        "description": "Package was marked as delivered but nothing arrived.",
        "is_unresolved": 1
    }])
    insert_tickets(sample_df, db_path=isolated_db)

    with patch.dict("os.environ", {"GEMINI_API_KEY": "dummy-key"}):
        with patch("google.genai.Client", side_effect=Exception("429 Resource has been exhausted (quota)")):
            report_res = generate_support_insights_report(db_path=isolated_db)
            assert report_res.is_fallback is True
            assert "Deterministic" in report_res.model_name
            assert "1 customer tickets" in report_res.content


# =====================================================================
# 5. FLASK REST API ERROR RESPONSES
# =====================================================================

def test_flask_csv_upload_empty_filename(client):
    """Verifies that an empty filename returns 400 Bad Request."""
    data = {"file": (io.BytesIO(b"data"), "")}
    response = client.post("/api/ingest/csv", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "No selected file" in response.get_json()["message"]


def test_flask_csv_upload_corrupted_data(client):
    """Verifies that uploading a completely invalid CSV returns 400 with errors list."""
    data = {"file": (io.BytesIO(b"not a csv file, invalid content"), "corrupted.csv")}
    response = client.post("/api/ingest/csv", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    res_json = response.get_json()
    assert res_json["status"] == "error"
    assert "errors" in res_json


def test_flask_api_ingest_bad_endpoint(client):
    """Verifies that calling /api/ingest/api with an unreachable URL returns 400 with stage_failed."""
    payload = {"api_url": "http://127.0.0.1:59998/invalid_path", "api_key": "any-key"}
    response = client.post("/api/ingest/api", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "stage_failed" in data


def test_flask_tickets_filtering_no_matches(client):
    """Verifies that searching for non-existent tickets returns 200 with empty list."""
    response = client.get("/api/tickets?search=non_existent_ticket_xyz_99999")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["count"] == 0
    assert data["tickets"] == []
