"""
Unit Tests for Flask Backend REST API
Module 8: React Frontend and Flask API Foundation
"""

import io
import pytest
from src.flask_app import app
from src.database import init_db, get_ticket_count


@pytest.fixture
def client():
    """Provides Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_flask_health_endpoint(client):
    """Verifies that /api/health returns 200 and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["database_connected"] is True


def test_flask_analytics_kpis_endpoint(client):
    """Verifies that /api/analytics/kpis returns calculated SQL analytics."""
    response = client.get("/api/analytics/kpis")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    kpis = json_data["data"]
    assert "total_tickets" in kpis
    assert "open_tickets" in kpis
    assert "avg_resolution_hours" in kpis
    assert isinstance(kpis["category_distribution"], list)
    assert isinstance(kpis["status_distribution"], list)


def test_flask_tickets_list_endpoint(client):
    """Verifies that /api/tickets returns records and filters."""
    response = client.get("/api/tickets?limit=10")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "success"
    assert "tickets" in json_data
    assert isinstance(json_data["tickets"], list)


def test_flask_csv_upload_missing_file(client):
    """Verifies that submitting without a file returns 400 Bad Request."""
    response = client.post("/api/ingest/csv")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "No file part" in data["message"]


def test_flask_csv_upload_valid_file(client):
    """Verifies uploading a CSV file processes through the full pipeline."""
    csv_bytes = (
        b"ticket_id,created_at,status,category,priority,subject,description\n"
        b"TKT-FLASK-1,2026-03-01 10:00:00,Open,Delivery & Shipping,High,Delay,Where is my parcel\n"
        b"TKT-FLASK-2,2026-03-01 11:00:00,Resolved,Billing & Refunds,Medium,Refund,Refund received\n"
    )

    data = {
        "file": (io.BytesIO(csv_bytes), "test_flask_tickets.csv")
    }

    response = client.post(
        "/api/ingest/csv",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200
    res_data = response.get_json()
    assert res_data["status"] == "success"
    assert "ingestion" in res_data
    assert "data_quality" in res_data
    assert "database" in res_data


def test_flask_ai_report_endpoint(client):
    """Verifies that /api/ai/report returns executive summary."""
    response = client.post("/api/ai/report")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "report" in data
    assert "is_fallback" in data
    assert "model_name" in data
    assert len(data["report"]) > 50
