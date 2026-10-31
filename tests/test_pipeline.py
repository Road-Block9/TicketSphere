"""
Unit Tests for End-to-End Pipeline Orchestrator
Module 10: Integrate the Complete Pipeline - TicketSphere
"""

import io
import pytest
import pandas as pd
from src.database import init_db, get_ticket_count
from src.pipeline import run_csv_pipeline, run_api_pipeline, run_full_pipeline_cycle


@pytest.fixture
def test_db(tmp_path):
    """Provides an isolated test database."""
    db_file = tmp_path / "test_pipeline.db"
    init_db(db_file)
    return db_file


def test_run_csv_pipeline_success(test_db):
    """Verifies that run_csv_pipeline executes validation, cleaning, storage, and KPI refresh."""
    sample_csv = (
        "ticket_id,created_at,resolved_at,status,category,priority,subject,description\n"
        "TKT-PIPE-1,2026-03-01 10:00:00,2026-03-01 14:00:00,Resolved,Technical Support,High,Bug,Crash\n"
        "TKT-PIPE-2,2026-03-01 11:00:00,,Open,Billing & Refunds,Critical,Invoice,Billing error\n"
    )

    result = run_csv_pipeline(io.StringIO(sample_csv), source_name="test_stream.csv", db_path=test_db)

    assert result["success"] is True
    assert result["stage_completed"] == "storage_and_analytics"
    assert result["ingestion"]["records_received"] == 2
    assert result["database"]["records_inserted"] == 2
    assert result["database"]["records_skipped_duplicate"] == 0
    assert result["database"]["total_in_db"] == 2

    # Verify updated KPIs
    kpis = result["updated_kpis"]
    assert kpis["total_tickets"] == 2
    assert kpis["open_tickets"] == 1
    assert kpis["unresolved_tickets"] == 1
    assert kpis["unresolved_rate_pct"] == 50.0
    assert kpis["critical_unresolved_count"] == 1


def test_run_csv_pipeline_duplicate_prevention(test_db):
    """Verifies that running the pipeline on the same file twice does not inflate ticket count."""
    sample_csv = (
        "ticket_id,created_at,resolved_at,status,category,priority,subject,description\n"
        "TKT-DUP-1,2026-03-01 10:00:00,2026-03-01 12:00:00,Resolved,Delivery & Shipping,Medium,Box,Late\n"
    )

    # First run: inserts 1 record
    res1 = run_csv_pipeline(io.StringIO(sample_csv), source_name="dup_test.csv", db_path=test_db)
    assert res1["database"]["records_inserted"] == 1
    assert res1["database"]["records_skipped_duplicate"] == 0
    assert get_ticket_count(test_db) == 1

    # Second run: identical ticket_id -> skipped 1 record, total remains 1
    res2 = run_csv_pipeline(io.StringIO(sample_csv), source_name="dup_test.csv", db_path=test_db)
    assert res2["database"]["records_inserted"] == 0
    assert res2["database"]["records_skipped_duplicate"] == 1
    assert get_ticket_count(test_db) == 1


def test_run_csv_pipeline_empty_file_handling(test_db):
    """Verifies that an empty CSV is rejected cleanly without modifying the database."""
    empty_csv = ""
    result = run_csv_pipeline(io.StringIO(empty_csv), source_name="empty.csv", db_path=test_db)

    assert result["success"] is False
    assert result["stage_failed"] == "ingestion_validation"
    assert get_ticket_count(test_db) == 0


def test_run_csv_pipeline_missing_columns(test_db):
    """Verifies that CSV with missing mandatory columns fails validation."""
    invalid_csv = "customer_name,notes\nJohn,Some note\n"
    result = run_csv_pipeline(io.StringIO(invalid_csv), source_name="invalid.csv", db_path=test_db)

    assert result["success"] is False
    assert result["stage_failed"] == "ingestion_validation"
    assert any("ticket_id" in err.lower() for err in result["errors"])
    assert get_ticket_count(test_db) == 0


def test_run_full_pipeline_cycle(test_db):
    """Verifies full execution cycle including GenAI report generation grounded in fresh metrics."""
    sample_csv = (
        "ticket_id,created_at,resolved_at,status,category,priority,subject,description\n"
        "TKT-FULL-1,2026-03-01 08:00:00,2026-03-01 16:00:00,Resolved,Technical Support,High,Login,Fixed\n"
        "TKT-FULL-2,2026-03-02 09:00:00,,Open,Technical Support,Critical,Crash,App down\n"
    )

    cycle_result = run_full_pipeline_cycle(io.StringIO(sample_csv), db_path=test_db)

    assert cycle_result["success"] is True
    assert "pipeline_outcome" in cycle_result
    assert "report" in cycle_result
    report = cycle_result["report"]
    assert len(report["content"]) > 100
    assert "disclaimer" in report
    assert report["generation_time_seconds"] >= 0.0


def test_run_api_pipeline_error_handling(test_db):
    """Verifies that an invalid API URL returns a clean failure rather than crashing."""
    result = run_api_pipeline(
        api_url="http://127.0.0.1:59999/non_existent_endpoint",
        api_key="fake-key",
        db_path=test_db
    )

    assert result["success"] is False
    assert "stage_failed" in result
