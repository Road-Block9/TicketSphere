"""
Unit Tests for API Data Ingestion Module
Module 6: Customer Support Ticket Analytics & GenAI Business Assistant
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests
from fastapi.testclient import TestClient

from src.mock_api import app, MOCK_API_TICKETS, EXPECTED_API_KEY
from src.api_client import fetch_tickets_from_api, ingest_api_pipeline, ApiIngestionResult
from src.database import init_db, get_ticket_count


@pytest.fixture
def api_test_client():
    """Provides a FastAPI in-memory TestClient for the mock server."""
    return TestClient(app)


def test_mock_api_health_endpoint(api_test_client):
    """Verifies the health check endpoint returns 200 and healthy status."""
    response = api_test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Simulated" in data["service"]


def test_mock_api_get_tickets(api_test_client):
    """Verifies that the mock API returns the expected tickets list."""
    response = api_test_client.get("/api/v1/tickets")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "tickets" in data
    assert len(data["tickets"]) == len(MOCK_API_TICKETS)


def test_mock_api_status_filtering(api_test_client):
    """Verifies that query parameters filter tickets accurately."""
    response = api_test_client.get("/api/v1/tickets?status=Open")
    assert response.status_code == 200
    data = response.json()
    for t in data["tickets"]:
        assert t["status"].lower() == "open"


def test_mock_api_invalid_api_key(api_test_client):
    """Verifies that an incorrect API key returns HTTP 401 Unauthorized."""
    response = api_test_client.get(
        "/api/v1/tickets",
        headers={"X-API-Key": "completely-invalid-key"}
    )
    assert response.status_code == 401
    assert "Unauthorized" in response.text or "Invalid" in response.text


def test_api_client_fetch_success():
    """Tests client parsing of a successful API response."""
    mock_payload = {
        "status": "success",
        "source": "SIMULATED_ENTERPRISE_API",
        "tickets": [
            {
                "ticket_id": "TKT-API-999",
                "customer_id": "CUST-999",
                "created_at": "2026-03-20 10:00:00",
                "resolved_at": None,
                "category": "Technical Support",
                "priority": "High",
                "status": "Open",
                "subject": "Webhook latency",
                "description": "High latency on webhook delivery",
                "resolution_notes": None
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("requests.get", return_value=mock_resp):
        res = fetch_tickets_from_api("http://mock-url/api/v1/tickets")
        assert res.success is True
        assert res.record_count == 1
        assert res.data is not None
        assert res.data["ticket_id"].iloc[0] == "TKT-API-999"


def test_api_client_connection_error_handling():
    """Tests graceful handling when API server is down (ConnectionError)."""
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Connection refused")):
        res = fetch_tickets_from_api("http://127.0.0.1:9999/api/v1/tickets")
        assert res.success is False
        assert res.data is None
        assert "Could not connect to API server" in res.error_message


def test_api_client_timeout_handling():
    """Tests graceful handling when API request times out."""
    with patch("requests.get", side_effect=requests.exceptions.Timeout("Timeout")):
        res = fetch_tickets_from_api("http://mock-url/api/v1/tickets", timeout=2)
        assert res.success is False
        assert "timed out" in res.error_message


def test_api_client_unauthorized_error():
    """Tests handling of 401 Unauthorized response from API."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"

    with patch("requests.get", return_value=mock_resp):
        res = fetch_tickets_from_api("http://mock-url/api/v1/tickets")
        assert res.success is False
        assert res.status_code == 401
        assert "Authentication failure" in res.error_message


def test_end_to_end_api_ingestion_pipeline(tmp_path):
    """Verifies that data fetched via API runs through Module 3 and Module 4 into SQLite."""
    temp_db = tmp_path / "pipeline_api_test.db"
    init_db(temp_db)

    mock_payload = {
        "status": "success",
        "source": "SIMULATED_ENTERPRISE_API",
        "tickets": [
            {
                "ticket_id": "TKT-E2E-API-1",
                "customer_id": "CUST-E2E-1",
                "created_at": "2026-03-18 09:00:00",
                "resolved_at": "2026-03-18 11:30:00",
                "category": "Delivery & Shipping",
                "priority": "High",
                "status": "Resolved",
                "subject": "Missing order tracking",
                "description": "Courier code not recognized",
                "resolution_notes": "Tracking refreshed"
            },
            {
                "ticket_id": "TKT-E2E-API-2",
                "customer_id": "CUST-E2E-2",
                "created_at": "2026-03-18 10:00:00",
                "resolved_at": None,
                "category": "Billing & Refunds",
                "priority": "Critical",
                "status": "Open",
                "subject": "Subscription overbilled",
                "description": "Billed twice in same month",
                "resolution_notes": None
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("requests.get", return_value=mock_resp):
        result = ingest_api_pipeline(api_url="http://mock-server/api/v1/tickets", db_path=temp_db)

        assert result["success"] is True
        assert result["inserted_count"] == 2
        assert result["skipped_count"] == 0
        assert get_ticket_count(temp_db) == 2

        # Verify duplicate prevention: Run again with same API payload
        result_2 = ingest_api_pipeline(api_url="http://mock-server/api/v1/tickets", db_path=temp_db)
        assert result_2["success"] is True
        assert result_2["inserted_count"] == 0
        assert result_2["skipped_count"] == 2
        assert get_ticket_count(temp_db) == 2  # Still 2, no duplicates!
