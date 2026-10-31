"""
Unit Tests for SQL Database and Storage Module
Module 4: Customer Support Ticket Analytics & GenAI Business Assistant
"""

import sqlite3
import pytest
import pandas as pd
from pathlib import Path
from src.database import (
    init_db,
    insert_tickets,
    get_ticket_count,
    get_all_tickets,
    execute_query,
    get_connection
)


@pytest.fixture
def temp_db(tmp_path):
    """Provides an isolated SQLite database file for each test."""
    db_file = tmp_path / "test_support.db"
    init_db(db_file)
    return db_file


@pytest.fixture
def sample_clean_df():
    """Provides a small clean DataFrame for database insertion tests."""
    return pd.DataFrame([
        {
            "ticket_id": "TKT-DB-1",
            "customer_id": "CUST-101",
            "created_at": "2026-03-01 10:00:00",
            "resolved_at": "2026-03-01 12:00:00",
            "category": "Delivery & Shipping",
            "priority": "High",
            "status": "Resolved",
            "subject": "Delayed parcel",
            "description": "Package delayed by courier",
            "resolution_notes": "Delivered",
            "resolution_time_hours": 2.0,
            "is_unresolved": 0
        },
        {
            "ticket_id": "TKT-DB-2",
            "customer_id": "CUST-102",
            "created_at": "2026-03-01 11:00:00",
            "resolved_at": None,
            "category": "Billing & Refunds",
            "priority": "Critical",
            "status": "Open",
            "subject": "Payment issue",
            "description": "Overcharged subscription",
            "resolution_notes": None,
            "resolution_time_hours": None,
            "is_unresolved": 1
        }
    ])


def test_init_db_creates_tables(temp_db):
    """Verifies that init_db creates tickets, ingestion_logs, and indexes."""
    with get_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert "tickets" in tables
        assert "ingestion_logs" in tables

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_tickets_status" in indexes
        assert "idx_tickets_category" in indexes


def test_insert_tickets_success(temp_db, sample_clean_df):
    """Verifies inserting clean tickets into SQLite."""
    inserted, skipped = insert_tickets(sample_clean_df, db_path=temp_db)
    assert inserted == 2
    assert skipped == 0
    assert get_ticket_count(temp_db) == 2


def test_duplicate_prevention_on_repeated_import(temp_db, sample_clean_df):
    """Verifies that importing the exact same dataset twice does NOT duplicate rows."""
    # First import
    inserted_1, skipped_1 = insert_tickets(sample_clean_df, db_path=temp_db)
    assert inserted_1 == 2
    assert skipped_1 == 0
    assert get_ticket_count(temp_db) == 2

    # Second import (same data)
    inserted_2, skipped_2 = insert_tickets(sample_clean_df, db_path=temp_db)
    assert inserted_2 == 0
    assert skipped_2 == 2
    assert get_ticket_count(temp_db) == 2  # Count must remain 2, not 4!


def test_get_all_tickets_retrieval(temp_db, sample_clean_df):
    """Verifies retrieving stored tickets as a pandas DataFrame."""
    insert_tickets(sample_clean_df, db_path=temp_db)
    retrieved = get_all_tickets(temp_db)

    assert isinstance(retrieved, pd.DataFrame)
    assert len(retrieved) == 2
    assert set(retrieved["ticket_id"]) == {"TKT-DB-1", "TKT-DB-2"}
    assert "resolution_time_hours" in retrieved.columns
    assert "is_unresolved" in retrieved.columns


def test_parameterised_query_execution(temp_db, sample_clean_df):
    """Verifies secure parameterised query execution."""
    insert_tickets(sample_clean_df, db_path=temp_db)

    # Parameterised query filtering by status
    query = "SELECT * FROM tickets WHERE status = ?;"
    open_tickets = execute_query(query, params=("Open",), db_path=temp_db)

    assert len(open_tickets) == 1
    assert open_tickets["ticket_id"].iloc[0] == "TKT-DB-2"
    assert open_tickets["is_unresolved"].iloc[0] == 1


def test_ingestion_log_recording(temp_db, sample_clean_df):
    """Verifies that each batch insertion writes a record to ingestion_logs."""
    insert_tickets(sample_clean_df, db_path=temp_db, source_name="batch_1.csv")

    with get_connection(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT source_name, total_received, records_inserted, records_skipped FROM ingestion_logs;")
        log_entry = cursor.fetchone()
        assert log_entry[0] == "batch_1.csv"
        assert log_entry[1] == 2
        assert log_entry[2] == 2
        assert log_entry[3] == 0
