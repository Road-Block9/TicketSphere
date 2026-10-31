"""
Unit Tests for SQL Analytics & Business Metrics Module
Module 5: Customer Support Ticket Analytics & GenAI Business Assistant
"""

import pytest
import pandas as pd
from pathlib import Path
from src.database import init_db, insert_tickets
from src.analytics import (
    query_total_tickets,
    query_category_distribution,
    query_status_distribution,
    query_resolution_time_metrics,
    query_unresolved_by_category,
    query_ticket_volume_trends,
    query_management_attention_tickets,
    get_all_analytics_kpis,
    format_analytics_summary_text,
)


@pytest.fixture
def analytics_db(tmp_path):
    """Initialises an isolated database populated with clean test tickets."""
    db_file = tmp_path / "analytics_test.db"
    init_db(db_file)

    test_tickets = pd.DataFrame([
        {
            "ticket_id": "TKT-A1",
            "customer_id": "C-1",
            "created_at": "2026-03-01 08:00:00",
            "resolved_at": "2026-03-01 12:00:00",
            "category": "Delivery & Shipping",
            "priority": "High",
            "status": "Resolved",
            "subject": "Delayed parcel",
            "description": "Courier delay",
            "resolution_notes": "Delivered",
            "resolution_time_hours": 4.0,
            "is_unresolved": 0
        },
        {
            "ticket_id": "TKT-A2",
            "customer_id": "C-2",
            "created_at": "2026-03-01 09:00:00",
            "resolved_at": "2026-03-01 15:00:00",
            "category": "Delivery & Shipping",
            "priority": "Medium",
            "status": "Closed",
            "subject": "Damaged box",
            "description": "Box crushed",
            "resolution_notes": "Coupon issued",
            "resolution_time_hours": 6.0,
            "is_unresolved": 0
        },
        {
            "ticket_id": "TKT-A3",
            "customer_id": "C-3",
            "created_at": "2026-03-02 10:00:00",
            "resolved_at": None,
            "category": "Technical Support",
            "priority": "Critical",
            "status": "Open",
            "subject": "App crash",
            "description": "Crash on login",
            "resolution_notes": None,
            "resolution_time_hours": None,
            "is_unresolved": 1
        },
        {
            "ticket_id": "TKT-A4",
            "customer_id": "C-4",
            "created_at": "2026-03-02 11:00:00",
            "resolved_at": None,
            "category": "Billing & Refunds",
            "priority": "Low",
            "status": "Pending",
            "subject": "Fee query",
            "description": "Question on tax",
            "resolution_notes": None,
            "resolution_time_hours": None,
            "is_unresolved": 1
        }
    ])

    insert_tickets(test_tickets, db_path=db_file)
    return db_file


def test_query_total_tickets(analytics_db):
    """Q1: Total tickets received."""
    total = query_total_tickets(db_path=analytics_db)
    assert total == 4


def test_query_category_distribution(analytics_db):
    """Q2: Most common categories and percentages."""
    df = query_category_distribution(db_path=analytics_db)
    assert len(df) == 3
    assert df["category"].iloc[0] == "Delivery & Shipping"
    assert df["ticket_count"].iloc[0] == 2
    assert df["percentage"].sum() == pytest.approx(100.0, rel=1e-2)


def test_query_status_distribution(analytics_db):
    """Q3: Ticket counts by status."""
    df = query_status_distribution(db_path=analytics_db)
    assert df["ticket_count"].sum() == 4
    statuses = set(df["status"])
    assert statuses == {"Resolved", "Closed", "Open", "Pending"}


def test_query_resolution_time_metrics(analytics_db):
    """Q4: Average resolution time calculations."""
    metrics = query_resolution_time_metrics(db_path=analytics_db)
    assert metrics["resolved_ticket_count"] == 2
    # (4.0 + 6.0) / 2 = 5.0 hours
    assert metrics["overall_avg_hours"] == 5.0
    assert metrics["overall_min_hours"] == 4.0
    assert metrics["overall_max_hours"] == 6.0


def test_query_unresolved_by_category(analytics_db):
    """Q5: Categories with most unresolved tickets."""
    df = query_unresolved_by_category(db_path=analytics_db)
    # Technical Support (1 unresolved) and Billing & Refunds (1 unresolved)
    assert df["unresolved_tickets"].sum() == 2
    for _, row in df.iterrows():
        assert row["unresolved_tickets"] + row["resolved_tickets"] == row["total_tickets"]


def test_query_ticket_volume_trends(analytics_db):
    """Q6: Temporal trends grouped by date."""
    df = query_ticket_volume_trends(db_path=analytics_db)
    assert len(df) == 2  # 2026-03-01 and 2026-03-02
    assert list(df["ticket_date"]) == ["2026-03-01", "2026-03-02"]
    assert df["total_volume"].sum() == 4


def test_query_management_attention_tickets(analytics_db):
    """Q7: Urgent management attention tickets (Critical/High & Unresolved)."""
    df = query_management_attention_tickets(db_path=analytics_db)
    # TKT-A3 is Critical & Open (unresolved).
    # TKT-A1 is High, but Resolved -> excluded.
    # TKT-A4 is Low & Pending -> excluded.
    assert len(df) == 1
    assert df["ticket_id"].iloc[0] == "TKT-A3"
    assert df["priority"].iloc[0] == "Critical"


def test_empty_database_analytics_handling(tmp_path):
    """Verifies that an empty database returns zeroed KPIs without division-by-zero crashes."""
    empty_db = tmp_path / "empty.db"
    init_db(empty_db)

    kpis = get_all_analytics_kpis(db_path=empty_db)
    assert kpis["total_tickets"] == 0
    assert kpis["unresolved_tickets"] == 0
    assert kpis["avg_resolution_hours"] == 0.0

    summary_text = format_analytics_summary_text(kpis)
    assert "No support ticket data available" in summary_text
