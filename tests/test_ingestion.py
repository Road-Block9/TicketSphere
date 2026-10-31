"""
Unit Tests for CSV Data Ingestion Module
Module 2: Customer Support Ticket Analytics & GenAI Business Assistant
"""

import io
import pytest
from pathlib import Path
import pandas as pd
from src.ingestion import read_csv_tickets, normalize_column_name, REQUIRED_COLUMNS


@pytest.fixture
def sample_csv_path():
    return Path("data/raw/customer_support_tickets.csv")


def test_valid_csv_ingestion(sample_csv_path):
    """Verifies that our valid 60-row sample dataset loads successfully."""
    result = read_csv_tickets(sample_csv_path)
    assert result.success is True
    assert result.record_count == 60
    assert result.data is not None
    assert len(result.errors) == 0
    for req in REQUIRED_COLUMNS:
        assert req in result.columns_found


def test_missing_file_handling():
    """Verifies that a non-existent file path fails gracefully with a clear message."""
    result = read_csv_tickets("data/raw/non_existent_tickets_xyz.csv")
    assert result.success is False
    assert result.data is None
    assert any("File not found" in err for err in result.errors)


def test_empty_file_handling(tmp_path):
    """Verifies that a 0-byte file fails gracefully."""
    empty_file = tmp_path / "empty_tickets.csv"
    empty_file.write_text("", encoding="utf-8")

    result = read_csv_tickets(empty_file)
    assert result.success is False
    assert any("is empty (0 bytes)" in err for err in result.errors)


def test_header_only_file_handling(tmp_path):
    """Verifies that a file with headers but zero records fails gracefully."""
    header_only = tmp_path / "headers_only.csv"
    header_only.write_text("ticket_id,created_at,status,category\n", encoding="utf-8")

    result = read_csv_tickets(header_only)
    assert result.success is False
    assert any("zero data records" in err for err in result.errors)


def test_missing_required_columns(tmp_path):
    """Verifies that missing core columns are correctly detected and reported."""
    invalid_csv = tmp_path / "invalid_columns.csv"
    # Missing 'ticket_id' and 'status'
    invalid_csv.write_text(
        "created_at,category,subject\n"
        "2026-03-01 10:00:00,Delivery,Lost parcel\n",
        encoding="utf-8"
    )

    result = read_csv_tickets(invalid_csv)
    assert result.success is False
    assert "ticket_id" in result.missing_required_columns
    assert "status" in result.missing_required_columns
    assert any("Missing required column(s)" in err for err in result.errors)


def test_column_alias_normalization():
    """Verifies that CRM export variations like 'Ticket ID' map to 'ticket_id'."""
    assert normalize_column_name("Ticket ID") == "ticket_id"
    assert normalize_column_name("Creation Date") == "created_at"
    assert normalize_column_name("State") == "status"
    assert normalize_column_name("Type") == "category"


def test_buffer_ingestion_for_streamlit():
    """Verifies that buffer streams (such as Streamlit UploadedFile) work seamlessly."""
    csv_content = (
        "ticket_id,created_at,status,category\n"
        "TKT-9901,2026-03-01 12:00:00,Open,Delivery\n"
        "TKT-9902,2026-03-01 13:00:00,Resolved,Billing\n"
    )
    buffer = io.StringIO(csv_content)
    result = read_csv_tickets(buffer)
    assert result.success is True
    assert result.record_count == 2
    assert result.data is not None
    assert list(result.data["ticket_id"]) == ["TKT-9901", "TKT-9902"]
