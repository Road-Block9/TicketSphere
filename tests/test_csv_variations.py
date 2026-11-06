"""
Tests for CSV Ingestion Pipeline Variations & Datetime Processing
Tests flexible column aliases, ExploreMyData, HowToCSV, Kaggle dataset schemas,
timezone consistency, datetime comparison fixes, and data integrity.
"""

import io
import pytest
import pandas as pd
from pathlib import Path

from src.ingestion import read_csv_tickets, normalize_column_name, COLUMN_ALIASES
from src.transformation import clean_and_transform_tickets, parse_datetime_series
from src.pipeline import run_csv_pipeline
from src.database import init_db, get_ticket_count, get_connection


@pytest.fixture
def temp_db(tmp_path):
    """Provides an isolated SQLite database path for testing."""
    db_file = tmp_path / "test_variations.db"
    init_db(db_file)
    return db_file


def test_column_name_normalization():
    """Tests whitespace trimming, lowercase conversion, and symbol normalization."""
    assert normalize_column_name("  Ticket ID  ") == "ticket_id"
    assert normalize_column_name("Ticket-Status") == "status"
    assert normalize_column_name("TICKET_TYPE") == "category"
    assert normalize_column_name("Created.Date") == "created_at"
    assert normalize_column_name("Time to Resolution") == "resolved_at"
    assert normalize_column_name("first_response_min") == "first_response_min"


def test_how_to_csv_sample_dataset():
    """
    Tests HowToCSV dataset (sample-support-tickets.csv):
    Contains ISO timestamps with UTC 'Z' suffix, csat, and resolved_at.
    """
    fixture_path = Path("tests/fixtures/sample-support-tickets.csv")
    assert fixture_path.exists(), "sample-support-tickets.csv fixture missing"

    result = read_csv_tickets(fixture_path)
    assert result.success is True
    assert result.data is not None
    assert len(result.data) == 280

    cleaned_df, report = clean_and_transform_tickets(result.data)
    assert report.accepted == 280
    assert report.rejected == 0
    assert report.date_anomalies == 0
    # Additional column csat preserved
    assert "csat" in cleaned_df.columns
    # Check resolution_time_hours computed for resolved tickets
    resolved_rows = cleaned_df[cleaned_df["status"].isin(["Resolved", "Closed"])]
    assert (resolved_rows["resolution_time_hours"] > 0).all()


def test_explore_my_data_dataset_no_invalid_comparison_error():
    """
    Tests ExploreMyData dataset (support-tickets-100.csv):
    Verifies that the previous 'TypeError: Invalid comparison between dtype=datetime64[ns] and DatetimeArray'
    is completely resolved, resolution_min is used to derive resolution times,
    and Open/Pending tickets remain unresolved without fabricated dates.
    """
    fixture_path = Path("tests/fixtures/support-tickets-100.csv")
    assert fixture_path.exists(), "support-tickets-100.csv fixture missing"

    result = read_csv_tickets(fixture_path)
    assert result.success is True
    assert result.data is not None
    assert len(result.data) == 100

    # Ensure no comparison exception is raised during transformation
    cleaned_df, report = clean_and_transform_tickets(result.data)
    assert report.accepted == 100
    assert report.rejected == 0
    assert report.date_anomalies == 0

    # Verify Open and Pending tickets have NO fabricated resolution time
    unresolved_rows = cleaned_df[cleaned_df["status"].isin(["Open", "Pending"])]
    assert len(unresolved_rows) == 21  # 14 open + 7 pending
    assert unresolved_rows["resolved_at"].isna().all()
    assert unresolved_rows["resolution_time_hours"].isna().all()
    assert (unresolved_rows["is_unresolved"] == 1).all()

    # Verify Closed and Resolved tickets have resolution_time_hours calculated from resolution_min
    resolved_rows = cleaned_df[cleaned_df["status"].isin(["Closed", "Resolved"])]
    assert len(resolved_rows) == 79  # 55 closed + 24 resolved
    assert resolved_rows["resolution_time_hours"].notna().all()
    assert (resolved_rows["resolution_time_hours"] > 0).all()
    assert (resolved_rows["is_unresolved"] == 0).all()

    # Additional columns preserved
    for extra_col in ["channel", "first_response_min", "resolution_min", "satisfaction"]:
        assert extra_col in cleaned_df.columns


def test_kaggle_missing_created_at_validation_error(temp_db):
    """
    Tests that a dataset genuinely lacking ticket created_at (e.g. Kaggle dataset
    with Date of Purchase instead) returns a clear validation error and
    leaves 0 records in SQLite.
    """
    fixture_path = Path("tests/fixtures/kaggle_explore_missing_created_at.csv")
    assert fixture_path.exists()

    result = read_csv_tickets(fixture_path)
    assert result.success is False
    assert any("Missing required column(s): created_at" in err for err in result.errors)

    # Verify pipeline fails safely and leaves no partial imports
    pipeline_res = run_csv_pipeline(str(fixture_path), db_path=temp_db)
    assert pipeline_res["success"] is False
    assert get_ticket_count(temp_db) == 0


def test_mixed_timezone_and_date_formats():
    """
    Tests handling of mixed date formats: ISO8601 with Z, timezone offsets (+05:30),
    standard naive formats, and invalid dates within the same dataset.
    """
    csv_data = """ticket_id,created_at,resolved_at,status,category
TKT-TZ-1,2026-01-01T00:00:00Z,2026-01-01T04:00:00Z,Resolved,Technical Support
TKT-TZ-2,2026-01-01 10:00:00+05:30,2026-01-01 12:30:00+05:30,Resolved,Billing
TKT-TZ-3,2026-01-01 08:00:00,2026-01-01 11:00:00,Closed,Delivery
TKT-BAD-DATE,invalid-date-string,2026-01-01 12:00:00,Resolved,Technical Support
"""
    result = read_csv_tickets(io.StringIO(csv_data))
    assert result.success is True
    assert len(result.data) == 4

    cleaned_df, report = clean_and_transform_tickets(result.data)
    # TKT-BAD-DATE must be rejected due to unparseable created_at
    assert report.rejected == 1
    assert report.accepted == 3
    assert "TKT-BAD-DATE" not in cleaned_df["ticket_id"].values

    # Check calculated resolution times
    row1 = cleaned_df[cleaned_df["ticket_id"] == "TKT-TZ-1"].iloc[0]
    assert row1["resolution_time_hours"] == 4.0

    row2 = cleaned_df[cleaned_df["ticket_id"] == "TKT-TZ-2"].iloc[0]
    assert row2["resolution_time_hours"] == 2.5

    row3 = cleaned_df[cleaned_df["ticket_id"] == "TKT-TZ-3"].iloc[0]
    assert row3["resolution_time_hours"] == 3.0


def test_column_aliases_and_case_insensitivity(temp_db):
    """
    Tests various column naming conventions: spaces, PascalCase, hyphenated, aliases.
    """
    csv_data = """Ticket ID,Ticket Date,Ticket Status,Ticket Type,Customer Email,Notes
TKT-ALIAS-01,2026-02-01 09:00:00,IN PROGRESS,BILLING & REFUNDS,user1@example.com,Customer called
TKT-ALIAS-02,2026-02-01 10:00:00,FIXED,DELIVERY,user2@example.com,Package redelivered
"""
    result = read_csv_tickets(io.StringIO(csv_data))
    assert result.success is True
    assert set(result.data.columns).issuperset({"ticket_id", "created_at", "status", "category"})

    cleaned_df, report = clean_and_transform_tickets(result.data)
    assert report.accepted == 2
    # Status standardisation check
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-ALIAS-01", "status"].iloc[0] == "Pending"
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-ALIAS-02", "status"].iloc[0] == "Resolved"
    # Category standardisation check
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-ALIAS-01", "category"].iloc[0] == "Billing & Refunds"
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-ALIAS-02", "category"].iloc[0] == "Delivery & Shipping"


def test_duplicate_detection_and_idempotent_ingestion(temp_db):
    """
    Tests that duplicate IDs within the CSV are deduplicated, and repeated pipeline runs
    do not inflate ticket counts (idempotent storage).
    """
    fixture_path = Path("tests/fixtures/support-tickets-100.csv")
    
    # Run pipeline first time
    res1 = run_csv_pipeline(str(fixture_path), db_path=temp_db)
    assert res1["success"] is True
    assert res1["database"]["records_inserted"] == 100
    assert get_ticket_count(temp_db) == 100

    # Run pipeline second time (duplicate file ingestion)
    res2 = run_csv_pipeline(str(fixture_path), db_path=temp_db)
    assert res2["success"] is True
    assert res2["database"]["records_inserted"] == 0
    assert res2["database"]["records_skipped_duplicate"] == 100
    assert get_ticket_count(temp_db) == 100


def test_flask_api_upload_both_datasets(tmp_path):
    """
    Tests Flask /api/ingest/csv endpoint with both HowToCSV and ExploreMyData datasets,
    as well as validation error responses for datasets with missing required columns.
    """
    import os
    os.environ["FLASK_ENV"] = "testing"
    from src.flask_app import app

    app.config["TESTING"] = True
    test_db = tmp_path / "flask_upload_test.db"
    app.config["DATABASE_PATH"] = test_db

    with app.test_client() as client:
        # 1. Upload HowToCSV dataset
        with open("tests/fixtures/sample-support-tickets.csv", "rb") as f:
            resp1 = client.post("/api/ingest/csv", data={"file": (f, "sample-support-tickets.csv")})
        assert resp1.status_code == 200
        json1 = resp1.get_json()
        assert json1["status"] == "success"
        assert json1["database"]["records_inserted"] == 280

        # 2. Upload ExploreMyData dataset
        with open("tests/fixtures/support-tickets-100.csv", "rb") as f:
            resp2 = client.post("/api/ingest/csv", data={"file": (f, "support-tickets-100.csv")})
        assert resp2.status_code == 200
        json2 = resp2.get_json()
        assert json2["status"] == "success"
        assert json2["database"]["records_inserted"] == 100

        # 3. Upload dataset missing created_at
        with open("tests/fixtures/kaggle_explore_missing_created_at.csv", "rb") as f:
            resp3 = client.post("/api/ingest/csv", data={"file": (f, "kaggle_missing.csv")})
        assert resp3.status_code == 400
        json3 = resp3.get_json()
        assert json3["status"] == "error"
        assert "Missing required column(s): created_at" in json3["errors"][0]


def test_database_persistence_and_duplicate_id_safety(tmp_path):
    """
    Audit Item 2: Verifies database persistence across restarts and duplicate prevention.
    - Inserting 280 tickets results in 280 rows.
    - Closing connection and reconnecting preserves all 280 rows.
    - Re-uploading the same 280-ticket file inserts 0 and skips 280 duplicates.
    - Uploading a file with genuinely new ticket IDs inserts only the new records.
    """
    db_file = tmp_path / "persist_audit.db"
    init_db(db_file)

    # First upload of 280-ticket sample
    res1 = run_csv_pipeline("tests/fixtures/sample-support-tickets.csv", db_path=db_file)
    assert res1["success"] is True
    assert res1["database"]["records_inserted"] == 280
    assert get_ticket_count(db_file) == 280

    # Simulate restart by connecting anew
    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        assert cursor.fetchone()[0] == 280

    # Re-upload same 280-ticket file: MUST insert 0 duplicates
    res2 = run_csv_pipeline("tests/fixtures/sample-support-tickets.csv", db_path=db_file)
    assert res2["success"] is True
    assert res2["database"]["records_inserted"] == 0
    assert res2["database"]["records_skipped_duplicate"] == 280
    assert get_ticket_count(db_file) == 280

    # Genuinely new ticket IDs file: MUST insert new records
    new_csv = tmp_path / "genuinely_new_tickets.csv"
    new_csv.write_text(
        "ticket_id,created_at,status,category,priority,subject,description\n"
        "TKT-AUDIT-NEW-01,2026-03-01 10:00:00,Open,Billing & Refunds,High,Invoice query,Need receipt\n"
        "TKT-AUDIT-NEW-02,2026-03-01 11:00:00,Closed,Technical Support,Medium,Bug,Fixed\n"
    )
    res3 = run_csv_pipeline(str(new_csv), db_path=db_file)
    assert res3["success"] is True
    assert res3["database"]["records_inserted"] == 2
    assert res3["database"]["records_skipped_duplicate"] == 0
    assert get_ticket_count(db_file) == 282


def test_genai_assistant_grounding_and_fallback_fidelity(temp_db):
    """
    Audit Item 4: Verifies AI Insights Assistant behavior:
    - In fallback mode (when no API key is set), displays deterministic fallback mode.
    - All metrics reported in the fallback text strictly match verified SQL analytics.
    - No fabricated ticket IDs, numbers, or categories appear.
    """
    from src.genai_assistant import generate_support_insights_report
    from src.analytics import get_all_analytics_kpis

    # Ingest sample tickets into temp DB
    run_csv_pipeline("tests/fixtures/sample-support-tickets.csv", db_path=temp_db)

    kpis = get_all_analytics_kpis(temp_db)
    report_res = generate_support_insights_report(kpis=kpis, db_path=str(temp_db))

    assert report_res.is_fallback is True
    assert "Deterministic Analytical" in report_res.model_name
    assert "Executive Support Insights Management Report" in report_res.content

    # Strict grounding assertions: verify metrics appear accurately in the generated report
    assert str(kpis["total_tickets"]) in report_res.content
    assert str(kpis["unresolved_tickets"]) in report_res.content
    assert str(kpis["unresolved_rate_pct"]) in report_res.content
    assert str(kpis["avg_resolution_hours"]) in report_res.content
