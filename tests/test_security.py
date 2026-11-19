"""
Security and Configuration Unit Tests
Covers SSRF validation, demo reset protection, Flask debug defaults,
CORS restrictions, file upload size limits, and API key handling.
"""

import io
import os
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask

from src.flask_app import app, is_demo_reset_enabled, get_allowed_cors_origins
from src.api_client import validate_api_url, fetch_tickets_from_api, ApiIngestionResult
from src.database import init_db, get_ticket_count, insert_tickets
import pandas as pd


@pytest.fixture
def test_db(tmp_path):
    """Isolated database for security testing."""
    db_file = tmp_path / "security_test.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def security_client(test_db):
    """Flask client with clean test config."""
    app.config["TESTING"] = True
    app.config["DATABASE_PATH"] = test_db
    # Reset config overrides
    app.config.pop("ENABLE_DEMO_RESET", None)
    app.config.pop("DEMO_RESET_TOKEN", None)
    with app.test_client() as client:
        yield client


# =====================================================================
# 1. SSRF VALIDATION & API INGESTION TESTS
# =====================================================================

def test_ssrf_rejects_disallowed_schemes():
    """Verify that schemes other than http and https are strictly rejected."""
    for bad_url in [
        "ftp://example.com/tickets.json",
        "file:///etc/passwd",
        "gopher://example.com:70/",
        "javascript:alert(1)",
        "data:text/plain;base64,SGVsbG8=",
    ]:
        is_valid, err = validate_api_url(bad_url)
        assert is_valid is False
        assert "scheme" in err.lower() or "disallowed" in err.lower()


def test_ssrf_rejects_embedded_credentials():
    """Verify that URLs with embedded user credentials (user:pass@host) are rejected."""
    is_valid, err = validate_api_url("http://admin:secret@example.com/api/v1/tickets")
    assert is_valid is False
    assert "credential" in err.lower() or "user" in err.lower()


def test_ssrf_rejects_cloud_metadata_endpoints(monkeypatch):
    """Verify that cloud metadata IPs and hostnames are rejected unconditionally."""
    metadata_targets = [
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.253/metadata",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://metadata/v1/",
        "http://instance-data/latest/meta-data/",
    ]
    # Even if local mock is allowed, cloud metadata must always be blocked
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "true")
    for target in metadata_targets:
        is_valid, err = validate_api_url(target)
        assert is_valid is False
        assert "metadata" in err.lower() or "prohibited" in err.lower() or "link-local" in err.lower()


def test_ssrf_rejects_localhost_in_production(monkeypatch):
    """Verify that localhost/loopback is rejected when ALLOW_LOCAL_MOCK_API=false."""
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "false")
    for target in [
        "http://127.0.0.1:8000/api/v1/tickets",
        "http://localhost:8000/api/v1/tickets",
        "http://[::1]:8000/api/v1/tickets",
    ]:
        is_valid, err = validate_api_url(target)
        assert is_valid is False
        assert "localhost" in err.lower() or "loopback" in err.lower() or "disallowed" in err.lower()


def test_ssrf_allows_localhost_in_development(monkeypatch):
    """Verify that localhost/127.0.0.1 is permitted when ALLOW_LOCAL_MOCK_API=true."""
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "true")
    is_valid, err = validate_api_url("http://127.0.0.1:8000/api/v1/tickets")
    assert is_valid is True
    assert err == ""


def test_ssrf_rejects_private_ips_in_production(monkeypatch):
    """Verify that private LAN addresses (RFC 1918) are rejected in production."""
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "false")
    for target in [
        "http://10.0.0.1:8080/tickets",
        "http://192.168.1.100:8000/tickets",
        "http://172.16.0.5:8000/tickets",
    ]:
        is_valid, err = validate_api_url(target)
        assert is_valid is False
        assert "private" in err.lower() or "internal" in err.lower()


def test_ssrf_allowlist_restriction(monkeypatch):
    """Verify that API_ALLOWED_HOSTS strictly confines target domains."""
    monkeypatch.setenv("API_ALLOWED_HOSTS", "api.trusted-partner.com,api.zendesk.com")
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "false")

    # Host not in allowlist
    is_valid, err = validate_api_url("https://malicious-site.com/tickets")
    assert is_valid is False
    assert "not in the configured api_allowed_hosts" in err.lower()


def test_ssrf_blocks_unsafe_redirect(monkeypatch):
    """Verify that a redirect pointing to cloud metadata is intercepted and blocked."""
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "true")

    # Initial response is a 302 redirecting to metadata
    mock_redirect_resp = MagicMock()
    mock_redirect_resp.is_redirect = True
    mock_redirect_resp.status_code = 302
    mock_redirect_resp.headers = {"Location": "http://169.254.169.254/latest/meta-data/"}

    with patch("src.api_client.requests.get", return_value=mock_redirect_resp):
        res = fetch_tickets_from_api("http://127.0.0.1:8000/api/v1/tickets")
        assert res.success is False
        assert "redirect destination blocked" in res.error_message.lower()


def test_flask_api_ingest_rejects_ssrf_url(security_client, monkeypatch):
    """Verify that /api/ingest/api returns HTTP 400 when an SSRF target is requested."""
    monkeypatch.setenv("ALLOW_LOCAL_MOCK_API", "true")
    payload = {"api_url": "http://169.254.169.254/latest/meta-data/", "api_key": ""}
    response = security_client.post("/api/ingest/api", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "stage_failed" in data


# =====================================================================
# 2. DATABASE RESET ENDPOINT PROTECTION TESTS
# =====================================================================

def test_demo_reset_disabled_by_default(security_client, test_db, monkeypatch):
    """Verify that /api/demo/reset returns HTTP 403 when ENABLE_DEMO_RESET is disabled."""
    monkeypatch.delenv("ENABLE_DEMO_RESET", raising=False)
    app.config.pop("ENABLE_DEMO_RESET", None)

    # Insert a sample ticket
    df = pd.DataFrame([{
        "ticket_id": "TKT-SEC-1",
        "customer_id": "CUST-1",
        "created_at": "2026-03-01 10:00:00",
        "resolved_at": None,
        "category": "Technical Support",
        "priority": "High",
        "status": "Open",
        "subject": "Security test",
        "description": "Test ticket",
        "resolution_notes": None,
        "resolution_time_hours": None,
        "is_unresolved": 1
    }])
    insert_tickets(df, db_path=test_db)
    assert get_ticket_count(test_db) == 1

    # Attempt reset
    response = security_client.post("/api/demo/reset")
    assert response.status_code == 403
    data = response.get_json()
    assert data["status"] == "error"
    assert "disabled" in data["message"].lower()

    # Database must remain untouched
    assert get_ticket_count(test_db) == 1


def test_demo_reset_enabled_without_token(security_client, test_db, monkeypatch):
    """Verify that /api/demo/reset succeeds when ENABLE_DEMO_RESET=true (local demo mode)."""
    monkeypatch.setenv("ENABLE_DEMO_RESET", "true")
    monkeypatch.delenv("DEMO_RESET_TOKEN", raising=False)
    app.config["ENABLE_DEMO_RESET"] = True
    app.config["DEMO_RESET_TOKEN"] = ""

    df = pd.DataFrame([{
        "ticket_id": "TKT-SEC-2",
        "customer_id": "CUST-2",
        "created_at": "2026-03-01 10:00:00",
        "resolved_at": None,
        "category": "Technical Support",
        "priority": "High",
        "status": "Open",
        "subject": "Security test",
        "description": "Test ticket",
        "resolution_notes": None,
        "resolution_time_hours": None,
        "is_unresolved": 1
    }])
    insert_tickets(df, db_path=test_db)
    assert get_ticket_count(test_db) == 1

    response = security_client.post("/api/demo/reset")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert get_ticket_count(test_db) == 0


def test_demo_reset_requires_valid_token_when_configured(security_client, test_db, monkeypatch):
    """Verify that /api/demo/reset enforces token authorization when DEMO_RESET_TOKEN is set."""
    token = "super-secret-admin-token-2026"
    monkeypatch.setenv("ENABLE_DEMO_RESET", "true")
    monkeypatch.setenv("DEMO_RESET_TOKEN", token)
    app.config["ENABLE_DEMO_RESET"] = True
    app.config["DEMO_RESET_TOKEN"] = token

    # 1. Missing token -> 401
    res_no_token = security_client.post("/api/demo/reset")
    assert res_no_token.status_code == 401
    assert "unauthorized" in res_no_token.get_json()["message"].lower()

    # 2. Wrong token -> 401
    res_bad_token = security_client.post(
        "/api/demo/reset",
        headers={"X-Reset-Token": "wrong-token"}
    )
    assert res_bad_token.status_code == 401

    # 3. Correct token via X-Reset-Token header -> 200
    res_good_header = security_client.post(
        "/api/demo/reset",
        headers={"X-Reset-Token": token}
    )
    assert res_good_header.status_code == 200
    assert res_good_header.get_json()["status"] == "success"

    # 4. Correct token via Bearer Authorization header -> 200
    res_bearer = security_client.post(
        "/api/demo/reset",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_bearer.status_code == 200


# =====================================================================
# 3. FLASK DEBUG MODE CONFIGURATION TESTS
# =====================================================================

def test_flask_debug_defaults_to_false(monkeypatch):
    """Verify that Flask debug mode defaults to False when FLASK_DEBUG is unset."""
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    assert debug_mode is False


def test_flask_debug_explicitly_enabled(monkeypatch):
    """Verify that FLASK_DEBUG=true enables debug mode."""
    monkeypatch.setenv("FLASK_DEBUG", "true")
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    assert debug_mode is True


# =====================================================================
# 4. CORS CONFIGURATION TESTS
# =====================================================================

def test_cors_default_origins():
    """Verify that default trusted origins include Vite local ports and exclude wildcards."""
    origins = get_allowed_cors_origins()
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins
    assert "*" not in origins


def test_cors_configurable_via_env(monkeypatch):
    """Verify that CORS_ALLOWED_ORIGINS appends custom trusted deployment domains."""
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://ticketsphere.example.com")
    origins = get_allowed_cors_origins()
    assert "https://ticketsphere.example.com" in origins
    assert "http://localhost:5173" in origins


def test_cors_preflight_response(security_client):
    """Verify that CORS headers are returned for allowed origins."""
    response = security_client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"


# =====================================================================
# 5. FILE UPLOAD SIZE LIMIT TESTS
# =====================================================================

def test_upload_exceeding_limit_returns_413(security_client):
    """Verify that files exceeding MAX_CONTENT_LENGTH return HTTP 413 with JSON error."""
    # Set limit to 100 KB for test
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024

    oversized_data = b"x" * (150 * 1024)
    data = {
        "file": (io.BytesIO(oversized_data), "too_large.csv")
    }
    response = security_client.post(
        "/api/ingest/csv",
        data=data,
        content_type="multipart/form-data"
    )
    assert response.status_code == 413
    res_json = response.get_json()
    assert res_json["status"] == "error"
    assert "exceeds" in res_json["message"].lower()

    # Restore default
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# =====================================================================
# 6. OPTIONAL API KEY HANDLING TESTS
# =====================================================================

def test_fetch_tickets_without_api_key_succeeds():
    """Verify that fetch_tickets_from_api works without sending an X-API-Key when none is given."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "success", "tickets": []}
    mock_resp.is_redirect = False

    with patch("src.api_client.requests.get", return_value=mock_resp) as mock_get:
        res = fetch_tickets_from_api("http://127.0.0.1:8000/api/v1/tickets", api_key="")
        assert res.success is True
        # Verify X-API-Key header was not attached
        sent_headers = mock_get.call_args[1].get("headers", {})
        assert "X-API-Key" not in sent_headers


def test_fetch_tickets_with_api_key_attaches_header():
    """Verify that fetch_tickets_from_api attaches X-API-Key header when key is provided."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "success", "tickets": []}
    mock_resp.is_redirect = False

    with patch("src.api_client.requests.get", return_value=mock_resp) as mock_get:
        res = fetch_tickets_from_api("http://127.0.0.1:8000/api/v1/tickets", api_key="my-custom-key")
        assert res.success is True
        sent_headers = mock_get.call_args[1].get("headers", {})
        assert sent_headers.get("X-API-Key") == "my-custom-key"
