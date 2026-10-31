"""
SQL Analytics and Business Metrics Module
Module 5: Customer Support Ticket Analytics & GenAI Business Assistant

Executes verified SQL analytical queries against the SQLite database to answer
the 7 core business questions defined in the capstone requirements:
1. Total tickets received
2. Common complaint categories (volume & share)
3. Ticket status distribution (Open, Pending, Resolved, Closed)
4. Average ticket resolution time (overall and by category)
5. Categories with highest unresolved ticket counts (hotspots)
6. Ticket volume trends over time
7. High-priority and critical issues requiring urgent management attention
"""

import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import execute_query, get_db_path, init_db


# =====================================================================
# INDIVIDUAL ANALYTICAL SQL QUERIES
# =====================================================================

def query_total_tickets(db_path: Optional[Union[str, Path]] = None) -> int:
    """Q1: How many tickets have been received?"""
    sql = "SELECT COUNT(*) AS total_tickets FROM tickets;"
    df = execute_query(sql, db_path=db_path)
    return int(df["total_tickets"].iloc[0]) if not df.empty else 0


def query_category_distribution(db_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Q2: Which complaint categories are most common?"""
    sql = """
        SELECT 
            category,
            COUNT(*) AS ticket_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tickets), 2) AS percentage
        FROM tickets
        GROUP BY category
        ORDER BY ticket_count DESC;
    """
    return execute_query(sql, db_path=db_path)


def query_status_distribution(db_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Q3: How many tickets are open, pending, resolved, or closed?"""
    sql = """
        SELECT 
            status,
            COUNT(*) AS ticket_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tickets), 2) AS percentage
        FROM tickets
        GROUP BY status
        ORDER BY ticket_count DESC;
    """
    return execute_query(sql, db_path=db_path)


def query_resolution_time_metrics(db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Q4: What is the average ticket resolution time overall and by category?"""
    overall_sql = """
        SELECT 
            COUNT(resolution_time_hours) AS resolved_count,
            ROUND(AVG(resolution_time_hours), 2) AS avg_hours,
            ROUND(MIN(resolution_time_hours), 2) AS min_hours,
            ROUND(MAX(resolution_time_hours), 2) AS max_hours
        FROM tickets
        WHERE resolution_time_hours IS NOT NULL;
    """
    by_category_sql = """
        SELECT 
            category,
            COUNT(resolution_time_hours) AS resolved_count,
            ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_hours
        FROM tickets
        WHERE resolution_time_hours IS NOT NULL
        GROUP BY category
        ORDER BY avg_resolution_hours DESC;
    """
    overall_df = execute_query(overall_sql, db_path=db_path)
    by_cat_df = execute_query(by_category_sql, db_path=db_path)

    if not overall_df.empty and overall_df["resolved_count"].iloc[0] > 0:
        avg_h = float(overall_df["avg_hours"].iloc[0])
        min_h = float(overall_df["min_hours"].iloc[0])
        max_h = float(overall_df["max_hours"].iloc[0])
        resolved_cnt = int(overall_df["resolved_count"].iloc[0])
    else:
        avg_h, min_h, max_h, resolved_cnt = 0.0, 0.0, 0.0, 0

    return {
        "overall_avg_hours": avg_h,
        "overall_min_hours": min_h,
        "overall_max_hours": max_h,
        "resolved_ticket_count": resolved_cnt,
        "by_category_df": by_cat_df
    }


def query_unresolved_by_category(db_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Q5: Which complaint categories have the most unresolved tickets?
    Unresolved tickets are defined as status IN ('Open', 'Pending') or is_unresolved = 1.
    """
    sql = """
        SELECT 
            category,
            COUNT(*) AS total_tickets,
            SUM(is_unresolved) AS unresolved_tickets,
            COUNT(*) - SUM(is_unresolved) AS resolved_tickets,
            ROUND(SUM(is_unresolved) * 100.0 / COUNT(*), 2) AS unresolved_rate_pct
        FROM tickets
        GROUP BY category
        ORDER BY unresolved_tickets DESC, unresolved_rate_pct DESC;
    """
    return execute_query(sql, db_path=db_path)


def query_ticket_volume_trends(db_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Q6: How have ticket volumes changed over time?"""
    sql = """
        SELECT 
            DATE(created_at) AS ticket_date,
            COUNT(*) AS total_volume,
            SUM(is_unresolved) AS unresolved_volume,
            COUNT(*) - SUM(is_unresolved) AS resolved_volume
        FROM tickets
        GROUP BY DATE(created_at)
        ORDER BY ticket_date ASC;
    """
    return execute_query(sql, db_path=db_path)


def query_management_attention_tickets(db_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Q7: Which priorities or issue categories deserve immediate management attention?
    Filters for unresolved tickets with Critical or High priority.
    """
    sql = """
        SELECT 
            ticket_id,
            priority,
            category,
            status,
            created_at,
            subject,
            description
        FROM tickets
        WHERE is_unresolved = 1 AND priority IN ('Critical', 'High')
        ORDER BY 
            CASE priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                ELSE 3 
            END,
            created_at ASC;
    """
    return execute_query(sql, db_path=db_path)


# =====================================================================
# AGGREGATED METRICS CONTAINER FOR STREAMLIT & GENAI
# =====================================================================

def get_all_analytics_kpis(db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Executes all 7 analytical queries and bundles the verified metrics into
    a single structured dictionary for dashboard visualisations and GenAI context.
    """
    init_db(db_path)

    total_tickets = query_total_tickets(db_path)
    if total_tickets == 0:
        return {
            "total_tickets": 0,
            "open_tickets": 0,
            "pending_tickets": 0,
            "resolved_tickets": 0,
            "closed_tickets": 0,
            "unresolved_tickets": 0,
            "unresolved_rate_pct": 0.0,
            "avg_resolution_hours": 0.0,
            "critical_unresolved_count": 0,
            "high_unresolved_count": 0,
            "category_distribution": pd.DataFrame(),
            "status_distribution": pd.DataFrame(),
            "resolution_metrics": {},
            "unresolved_by_category": pd.DataFrame(),
            "volume_trends": pd.DataFrame(),
            "management_attention_tickets": pd.DataFrame(),
        }

    status_df = query_status_distribution(db_path)
    category_df = query_category_distribution(db_path)
    res_metrics = query_resolution_time_metrics(db_path)
    unresolved_df = query_unresolved_by_category(db_path)
    trends_df = query_ticket_volume_trends(db_path)
    urgent_df = query_management_attention_tickets(db_path)

    # Extract scalar status counts safely
    status_map = dict(zip(status_df["status"], status_df["ticket_count"]))
    open_cnt = int(status_map.get("Open", 0))
    pending_cnt = int(status_map.get("Pending", 0))
    resolved_cnt = int(status_map.get("Resolved", 0))
    closed_cnt = int(status_map.get("Closed", 0))
    unresolved_total = open_cnt + pending_cnt
    unresolved_rate = round((unresolved_total / total_tickets) * 100.0, 2)

    # Count urgent tickets
    critical_unresolved = len(urgent_df[urgent_df["priority"] == "Critical"]) if not urgent_df.empty else 0
    high_unresolved = len(urgent_df[urgent_df["priority"] == "High"]) if not urgent_df.empty else 0

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_cnt,
        "pending_tickets": pending_cnt,
        "resolved_tickets": resolved_cnt,
        "closed_tickets": closed_cnt,
        "unresolved_tickets": unresolved_total,
        "unresolved_rate_pct": unresolved_rate,
        "avg_resolution_hours": res_metrics.get("overall_avg_hours", 0.0),
        "critical_unresolved_count": critical_unresolved,
        "high_unresolved_count": high_unresolved,
        "category_distribution": category_df,
        "status_distribution": status_df,
        "resolution_metrics": res_metrics,
        "unresolved_by_category": unresolved_df,
        "volume_trends": trends_df,
        "management_attention_tickets": urgent_df,
    }


def format_analytics_summary_text(kpis: Dict[str, Any]) -> str:
    """
    Formats the verified analytical KPI results into a clean, structured text digest.
    This serves as the factual grounding context provided to the GenAI prompt.
    """
    if kpis.get("total_tickets", 0) == 0:
        return "No support ticket data available in database."

    lines = [
        "VERIFIED BUSINESS ANALYTICS METRICS",
        "=" * 60,
        f"• Total Tickets Ingested       : {kpis['total_tickets']}",
        f"• Open Tickets                 : {kpis['open_tickets']}",
        f"• Pending Tickets              : {kpis['pending_tickets']}",
        f"• Resolved Tickets             : {kpis['resolved_tickets']}",
        f"• Closed Tickets               : {kpis['closed_tickets']}",
        f"• Total Unresolved             : {kpis['unresolved_tickets']} ({kpis['unresolved_rate_pct']}%)",
        f"• Overall Avg Resolution Time  : {kpis['avg_resolution_hours']} hours",
        f"• Urgent Unresolved Tickets    : {kpis['critical_unresolved_count']} Critical, {kpis['high_unresolved_count']} High",
        "",
        "CATEGORY DISTRIBUTION (Total Tickets & Share):"
    ]
    for _, row in kpis["category_distribution"].iterrows():
        lines.append(f"  - {row['category']:<24}: {row['ticket_count']:>2} tickets ({row['percentage']}%)")

    lines.append("\nUNRESOLVED TICKETS BY CATEGORY (Hotspots):")
    for _, row in kpis["unresolved_by_category"].iterrows():
        lines.append(
            f"  - {row['category']:<24}: {int(row['unresolved_tickets']):>2} unresolved "
            f"({row['unresolved_rate_pct']}% backlog rate)"
        )

    lines.append("\nAVERAGE RESOLUTION TIME BY CATEGORY:")
    by_cat_df = kpis.get("resolution_metrics", {}).get("by_category_df", pd.DataFrame())
    if not by_cat_df.empty:
        for _, row in by_cat_df.iterrows():
            lines.append(f"  - {row['category']:<24}: {row['avg_resolution_hours']} hours")

    lines.append("\nTOP CRITICAL / HIGH UNRESOLVED ISSUES:")
    urgent_df = kpis.get("management_attention_tickets", pd.DataFrame())
    if not urgent_df.empty:
        for _, row in urgent_df.head(5).iterrows():
            lines.append(f"  - [{row['priority']}] {row['ticket_id']}: {row['subject']} ({row['category']})")
    else:
        lines.append("  - None")

    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    kpis = get_all_analytics_kpis()
    summary = format_analytics_summary_text(kpis)
    print(summary)
