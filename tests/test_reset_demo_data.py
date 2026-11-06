"""
Unit and Integration Tests for Reset Demo Data Feature
Validates safe, transactional demo data restoration in TicketSphere.
"""

import sqlite3
import pytest
import pandas as pd
from unittest.mock import patch

from src.database import (
    init_db,
    insert_tickets,
    get_ticket_count,
    get_all_tickets,
    get_connection,
    reset_demo_data,
)
from src.pipeline import run_csv_pipeline
from src.analytics import get_all_analytics_kpis
from src.genai_assistant import generate_support_insights_report
from src.flask_app import app


@pytest.fixture
def temp_db(tmp_path):
    """Provides an isolated SQLite database file for each test."""
    db_file = tmp_path / "test_reset_demo.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_csv(tmp_path):
    """Creates a realistic sample CSV for testing ingestion and reset."""
    csv_file = tmp_path / "sample_tickets.csv"
    csv_content = (
        "ticket_id,customer_id,created_at,resolved_at,category,priority,status,subject,description,resolution_notes\n"
        "TKT-R1,CUST-01,2026-03-01 09:00:00,2026-03-01 11:00:00,Delivery & Shipping,High,Resolved,Delayed package,Customer inquiry,Delivered safely\n"
        "TKT-R2,CUST-02,2026-03-01 10:00:00,,Billing & Refunds,Critical,Open,Overcharged on invoice,Double charge reported,\n"
        "TKT-R3,CUST-03,2026-03-02 08:30:00,2026-03-02 12:30:00,Technical Support,Medium,Closed,Password reset,Self service portal,Token generated\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file


@pytest.fixture
def flask_test_client(temp_db):
    """Provides a Flask test client configured with an isolated temporary database."""
    app.config["TESTING"] = True
    app.config["DATABASE_PATH"] = temp_db
    with app.test_client() as client:
        yield client


# Scenario 1: Initial reset works when database contains demo tickets
def test_initial_reset_when_database_has_records(temp_db, sample_csv):
    """Scenario 1: Reset removes all tickets and logs when database contains records."""
    # Ingest data first
    res = run_csv_pipeline(sample_csv, source_name="sample_tickets.csv", db_path=temp_db)
    assert res["success"] is True
    assert get_ticket_count(temp_db) == 3

    # Reset demo data
    reset_res = reset_demo_data(temp_db)
    assert reset_res["success"] is True
    assert reset_res["tickets_deleted"] == 3
    assert reset_res["logs_deleted"] >= 1
    assert reset_res["remaining_tickets"] == 0
    assert get_ticket_count(temp_db) == 0


# Scenario 2: Repeated reset succeeds safely without errors
def test_repeated_reset_idempotent(temp_db):
    """Scenario 2: Resetting an already clean database is idempotent and safe."""
    assert get_ticket_count(temp_db) == 0

    first_reset = reset_demo_data(temp_db)
    assert first_reset["success"] is True
    assert first_reset["tickets_deleted"] == 0
    assert first_reset["remaining_tickets"] == 0

    second_reset = reset_demo_data(temp_db)
    assert second_reset["success"] is True
    assert second_reset["tickets_deleted"] == 0
    assert second_reset["remaining_tickets"] == 0
    assert get_ticket_count(temp_db) == 0


# Scenario 3: Re-ingestion after reset inserts expected records (not duplicates)
def test_reingestion_after_reset(temp_db, sample_csv):
    """Scenario 3: After reset, re-uploading the same CSV inserts all records cleanly."""
    # First ingestion
    first_run = run_csv_pipeline(sample_csv, source_name="batch_1.csv", db_path=temp_db)
    assert first_run["database"]["records_inserted"] == 3
    assert first_run["database"]["records_skipped_duplicate"] == 0
    assert get_ticket_count(temp_db) == 3

    # Reset demo data
    reset_res = reset_demo_data(temp_db)
    assert reset_res["remaining_tickets"] == 0

    # Second ingestion with identical dataset
    second_run = run_csv_pipeline(sample_csv, source_name="batch_1.csv", db_path=temp_db)
    assert second_run["database"]["records_inserted"] == 3
    assert second_run["database"]["records_skipped_duplicate"] == 0
    assert get_ticket_count(temp_db) == 3


# Scenario 4: Duplicate protection without reset still skips existing ticket IDs
def test_duplicate_protection_preserved_without_reset(temp_db, sample_csv):
    """Scenario 4: Re-uploading without reset skips all duplicate ticket IDs."""
    first_run = run_csv_pipeline(sample_csv, source_name="batch.csv", db_path=temp_db)
    assert first_run["database"]["records_inserted"] == 3

    # Upload again without reset
    duplicate_run = run_csv_pipeline(sample_csv, source_name="batch.csv", db_path=temp_db)
    assert duplicate_run["database"]["records_inserted"] == 0
    assert duplicate_run["database"]["records_skipped_duplicate"] == 3
    assert get_ticket_count(temp_db) == 3


# Scenario 5: Analytics reflect actual database state after reset and re-ingestion
def test_analytics_metrics_after_reset_and_reingestion(temp_db, sample_csv):
    """Scenario 5: Analytics KPIs zero out on reset and accurately compute on re-ingestion."""
    run_csv_pipeline(sample_csv, db_path=temp_db)
    kpis_before = get_all_analytics_kpis(db_path=temp_db)
    assert kpis_before["total_tickets"] == 3
    assert kpis_before["unresolved_tickets"] == 1

    # Reset
    reset_demo_data(temp_db)
    kpis_empty = get_all_analytics_kpis(db_path=temp_db)
    assert kpis_empty["total_tickets"] == 0
    assert kpis_empty["unresolved_tickets"] == 0
    assert kpis_empty["avg_resolution_hours"] == 0.0

    # Re-ingest
    run_csv_pipeline(sample_csv, db_path=temp_db)
    kpis_after = get_all_analytics_kpis(db_path=temp_db)
    assert kpis_after["total_tickets"] == 3
    assert kpis_after["unresolved_tickets"] == 1
    assert kpis_after["avg_resolution_hours"] > 0


# Scenario 6: No orphaned records, schema and indexes remain intact
def test_schema_and_indexes_intact_after_reset(temp_db, sample_csv):
    """Scenario 6: Verifies schema, indexes, and table definitions remain intact after reset."""
    run_csv_pipeline(sample_csv, db_path=temp_db)
    reset_demo_data(temp_db)

    with get_connection(temp_db) as conn:
        cursor = conn.cursor()

        # Check tables still exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = {row[0] for row in cursor.fetchall()}
        assert "tickets" in tables
        assert "ingestion_logs" in tables

        # Check indexes still exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_tickets_status" in indexes
        assert "idx_tickets_category" in indexes
        assert "idx_tickets_created_at" in indexes
        assert "idx_tickets_priority" in indexes
        assert "idx_tickets_unresolved" in indexes

        # Check foreign keys pragma is active
        cursor.execute("PRAGMA foreign_keys;")
        assert cursor.fetchone()[0] == 1


# Scenario 7: Failure handling and transaction rollback
def test_reset_transaction_rollback_on_failure(temp_db, sample_csv):
    """Scenario 7: Transaction rolls back if an error occurs during reset, preventing partial state."""
    run_csv_pipeline(sample_csv, db_path=temp_db)
    assert get_ticket_count(temp_db) == 3

    class FailingCursor:
        def __init__(self, cursor):
            self._c = cursor

        def execute(self, sql, params=()):
            if "DELETE FROM tickets" in sql:
                raise sqlite3.OperationalError("Simulated write lock error")
            return self._c.execute(sql, params)

        def fetchone(self):
            return self._c.fetchone()

        def fetchall(self):
            return self._c.fetchall()

    class FailingConnection:
        def __init__(self, conn):
            self._conn = conn

        def cursor(self):
            return FailingCursor(self._conn.cursor())

        def commit(self):
            self._conn.commit()

        def rollback(self):
            self._conn.rollback()

        def close(self):
            self._conn.close()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()

    with patch("src.database.get_connection", side_effect=lambda path: FailingConnection(get_connection(path))):
        with pytest.raises(RuntimeError, match="Database reset transaction failed"):
            reset_demo_data(temp_db)

    # Verification: tickets must still exist because transaction rolled back
    assert get_ticket_count(temp_db) == 3


# Scenario 8: Flask REST API /api/demo/reset endpoint success
def test_flask_reset_endpoint_success(flask_test_client, temp_db, sample_csv):
    """Scenario 8: POST /api/demo/reset returns 200 and accurate reset statistics."""
    run_csv_pipeline(sample_csv, db_path=temp_db)
    assert get_ticket_count(temp_db) == 3

    response = flask_test_client.post("/api/demo/reset")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["tickets_deleted"] == 3
    assert data["data"]["remaining_tickets"] == 0
    assert get_ticket_count(temp_db) == 0


# Scenario 9: Flask REST API error handling
def test_flask_reset_endpoint_error_handling(flask_test_client):
    """Scenario 9: POST /api/demo/reset returns 500 when database reset encounters an error."""
    with patch("src.flask_app.reset_demo_data", side_effect=RuntimeError("Simulated DB disk failure")):
        response = flask_test_client.post("/api/demo/reset")
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"
        assert "Failed to reset demo data" in data["message"]


# Scenario 10: Downstream workflows (search, filters, GenAI) continue cleanly after reset
def test_downstream_workflows_after_reset(temp_db, sample_csv):
    """Scenario 10: Search, filters, and GenAI report generation continue to operate without crashing after reset."""
    run_csv_pipeline(sample_csv, db_path=temp_db)
    reset_demo_data(temp_db)

    # Stored tickets query returns empty DataFrame without errors
    tickets_df = get_all_tickets(temp_db)
    assert tickets_df.empty

    # Analytics returns zeroed KPIs
    kpis = get_all_analytics_kpis(db_path=temp_db)
    assert kpis["total_tickets"] == 0

    # GenAI report generator operates in deterministic fallback without crashing
    report = generate_support_insights_report(db_path=temp_db)
    assert report.is_fallback is True
    assert "0 customer tickets" in report.content or "0" in str(report.metrics.get("total_tickets"))


# Scenario 11: Persistence across connection restarts
def test_reset_persistence_across_connections(temp_db, sample_csv):
    """Scenario 11: Reset state persists across distinct connections and simulated app restarts."""
    run_csv_pipeline(sample_csv, db_path=temp_db)
    assert get_ticket_count(temp_db) == 3

    reset_demo_data(temp_db)

    # Open completely new connection to verify persistence
    with get_connection(temp_db) as new_conn:
        cursor = new_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM ingestion_logs;")
        assert cursor.fetchone()[0] == 0
