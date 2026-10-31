"""
Unit Tests for Data Transformation & Quality Module
Module 3: Customer Support Ticket Analytics & GenAI Business Assistant
"""

import pytest
import pandas as pd
import numpy as np
from src.transformation import clean_and_transform_tickets, DataQualityReport


def test_clean_sample_dataset():
    """Tests transformation on the 60-ticket sample dataset."""
    from src.ingestion import read_csv_tickets
    ingestion_res = read_csv_tickets("data/raw/customer_support_tickets.csv")
    assert ingestion_res.success is True

    cleaned_df, report = clean_and_transform_tickets(ingestion_res.data)
    assert len(cleaned_df) == 60
    assert report.total_received == 60
    assert report.accepted == 60
    assert report.rejected == 0
    assert report.duplicates_dropped == 0
    assert "resolution_time_hours" in cleaned_df.columns
    assert "is_unresolved" in cleaned_df.columns

    # Verify that unresolved tickets strictly have NaN resolution_time_hours
    open_tickets = cleaned_df[cleaned_df["status"].isin(["Open", "Pending"])]
    assert open_tickets["resolution_time_hours"].isna().all()
    assert (open_tickets["is_unresolved"] == 1).all()

    # Verify resolved tickets have calculated resolution_time_hours
    resolved_tickets = cleaned_df[cleaned_df["status"].isin(["Resolved", "Closed"])]
    assert resolved_tickets["resolution_time_hours"].notna().all()
    assert (resolved_tickets["is_unresolved"] == 0).all()
    assert (resolved_tickets["resolution_time_hours"] > 0).all()


def test_duplicate_ticket_removal():
    """Tests that duplicate ticket IDs are removed and recorded in the DQ report."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-DUP-1",
            "created_at": "2026-03-01 10:00:00",
            "status": "Open",
            "category": "Delivery & Shipping",
            "subject": "First copy",
        },
        {
            "ticket_id": "TKT-DUP-1",
            "created_at": "2026-03-01 10:00:00",
            "status": "Open",
            "category": "Delivery & Shipping",
            "subject": "Duplicate copy",
        },
        {
            "ticket_id": "TKT-DUP-2",
            "created_at": "2026-03-01 11:00:00",
            "status": "Resolved",
            "category": "Billing & Refunds",
            "resolved_at": "2026-03-01 13:00:00",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert len(cleaned_df) == 2
    assert report.duplicates_dropped == 1
    assert report.accepted == 2


def test_missing_ticket_id_rejection():
    """Tests that records with missing ticket_id are rejected."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": None,
            "created_at": "2026-03-01 10:00:00",
            "status": "Open",
            "category": "Delivery",
        },
        {
            "ticket_id": "TKT-VALID-1",
            "created_at": "2026-03-01 10:00:00",
            "status": "Open",
            "category": "Delivery",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert len(cleaned_df) == 1
    assert report.rejected == 1
    assert any("ticket_id" in log["reason"] for log in report.rejection_log)


def test_unparseable_created_at_rejection():
    """Tests that records with corrupted created_at timestamps are rejected."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-BAD-DATE",
            "created_at": "invalid_date_xyz",
            "status": "Open",
            "category": "Technical Support",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert len(cleaned_df) == 0
    assert report.rejected == 1
    assert any("creation timestamp" in log["reason"] for log in report.rejection_log)


def test_status_and_category_standardisation():
    """Tests normalisation of statuses, categories, and priorities."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-NORM-1",
            "created_at": "2026-03-01 10:00:00",
            "status": "open",
            "category": "tech support",
            "priority": "urgent",
        },
        {
            "ticket_id": "TKT-NORM-2",
            "created_at": "2026-03-01 11:00:00",
            "status": "in_progress",
            "category": "shipping",
            "priority": "minor",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-NORM-1", "status"].iloc[0] == "Open"
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-NORM-1", "category"].iloc[0] == "Technical Support"
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-NORM-1", "priority"].iloc[0] == "Critical"

    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-NORM-2", "status"].iloc[0] == "Pending"
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-NORM-2", "category"].iloc[0] == "Delivery & Shipping"
    assert cleaned_df.loc[cleaned_df["ticket_id"] == "TKT-NORM-2", "priority"].iloc[0] == "Low"


def test_resolution_time_calculation():
    """Tests precise resolution time calculation in hours."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-TIME-1",
            "created_at": "2026-03-01 10:00:00",
            "resolved_at": "2026-03-01 13:30:00",
            "status": "Resolved",
            "category": "Billing & Refunds",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    # 3.5 hours = 3 hours and 30 minutes
    assert cleaned_df["resolution_time_hours"].iloc[0] == 3.5
    assert cleaned_df["is_unresolved"].iloc[0] == 0


def test_false_resolution_date_cleared_for_open_tickets():
    """Tests that an Open ticket with an accidental resolution date has it cleared."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-OPEN-FAKE-RES",
            "created_at": "2026-03-01 10:00:00",
            "resolved_at": "2026-03-01 12:00:00",
            "status": "Open",
            "category": "Technical Support",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert cleaned_df["resolved_at"].iloc[0] is None
    assert cleaned_df["resolution_time_hours"].isna().iloc[0]
    assert cleaned_df["is_unresolved"].iloc[0] == 1
    assert report.date_anomalies == 1


def test_negative_duration_handling():
    """Tests that tickets with resolved_at earlier than created_at are caught as anomalies."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-NEG-DUR",
            "created_at": "2026-03-02 10:00:00",
            "resolved_at": "2026-03-01 10:00:00",  # resolved before creation!
            "status": "Resolved",
            "category": "Billing",
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert cleaned_df["resolution_time_hours"].isna().iloc[0]
    assert report.date_anomalies == 1


def test_missing_string_imputation():
    """Tests that missing descriptions, subjects, and customer IDs receive sensible defaults."""
    raw_data = pd.DataFrame([
        {
            "ticket_id": "TKT-MISSING-STR",
            "created_at": "2026-03-01 10:00:00",
            "status": "Open",
            "category": "Customer Service",
            "customer_id": None,
            "subject": None,
            "description": None,
        }
    ])

    cleaned_df, report = clean_and_transform_tickets(raw_data)
    assert cleaned_df["customer_id"].iloc[0] == "CUST-UNKNOWN"
    assert cleaned_df["subject"].iloc[0] == "No Subject Provided"
    assert cleaned_df["description"].iloc[0] == "No Description Provided"
    assert "imputed_subject" in report.imputed_fields
    assert "imputed_description" in report.imputed_fields
