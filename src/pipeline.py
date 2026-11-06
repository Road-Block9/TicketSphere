"""
End-to-End Coordinated Pipeline Orchestration Module
Module 10: Integrate the Complete Pipeline - TicketSphere

Coordinates the complete workflow across Modules 1 to 9:
1. Ingestion (file/stream validation via Module 2 or HTTP API fetch via Module 6)
2. Cleaning & Transformation (deduplication, standardisation, duration math via Module 3)
3. Idempotent Storage (duplicate prevention via SQLite PRIMARY KEY in Module 4)
4. Analytics Calculation (verified SQL metrics via Module 5 & Module 9)
5. GenAI Executive Reporting (grounded management intelligence via Module 7)
"""

import sys
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import read_csv_tickets, IngestionResult
from src.transformation import clean_and_transform_tickets, DataQualityReport
from src.database import (
    init_db,
    insert_tickets,
    get_ticket_count,
    get_all_tickets,
    get_db_path,
)
from src.analytics import get_all_analytics_kpis
from src.api_client import ingest_api_pipeline, DEFAULT_API_URL, DEFAULT_API_KEY
from src.genai_assistant import generate_support_insights_report, GenAIReportResult


def run_csv_pipeline(
    file_or_stream: Union[str, Path, Any],
    source_name: str = "uploaded_file.csv",
    db_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Coordinates the full CSV ingestion, transformation, storage, and analytics refresh pipeline.
    
    Returns a unified status dictionary:
    - success: bool
    - message: str
    - stage_completed: str
    - ingestion: dict (records_received, columns_found, warnings)
    - data_quality: dict (accepted, corrected, rejected, duplicates_removed)
    - database: dict (records_inserted, records_skipped_duplicate, total_in_db)
    - updated_kpis: dict (total_tickets, open_tickets, unresolved_rate_pct, avg_resolution_hours)
    """
    init_db(db_path)

    # Stage 1: Ingestion & Schema Validation (Module 2)
    ingestion_res: IngestionResult = read_csv_tickets(file_or_stream)
    if not ingestion_res.success or ingestion_res.data is None:
        return {
            "success": False,
            "message": "CSV Ingestion validation failed.",
            "stage_failed": "ingestion_validation",
            "errors": ingestion_res.errors,
            "warnings": ingestion_res.warnings,
            "data_quality": {},
            "database": {
                "records_inserted": 0,
                "records_skipped_duplicate": 0,
                "total_in_db": get_ticket_count(db_path),
            },
            "updated_kpis": None,
        }

    # Stage 2: Data Cleaning & Transformation (Module 3)
    cleaned_df, dq_report = clean_and_transform_tickets(ingestion_res.data)

    # Stage 3: Idempotent Database Storage & Duplicate Prevention (Module 4)
    inserted, skipped = insert_tickets(
        cleaned_df, source_name=source_name, db_path=db_path
    )
    total_in_db = get_ticket_count(db_path)

    # Stage 4: Analytics Refresh (Module 5 & Module 9)
    fresh_kpis = get_all_analytics_kpis(db_path=db_path)

    return {
        "success": True,
        "message": f"Successfully processed '{source_name}': {inserted} inserted, {skipped} duplicate(s) skipped.",
        "stage_completed": "storage_and_analytics",
        "ingestion": {
            "records_received": ingestion_res.record_count,
            "columns_found": ingestion_res.columns_found,
            "warnings": ingestion_res.warnings,
        },
        "data_quality": dq_report.to_dict(),
        "database": {
            "records_inserted": inserted,
            "records_skipped_duplicate": skipped,
            "total_in_db": total_in_db,
        },
        "updated_kpis": {
            "total_tickets": fresh_kpis["total_tickets"],
            "open_tickets": fresh_kpis["open_tickets"],
            "unresolved_tickets": fresh_kpis["unresolved_tickets"],
            "unresolved_rate_pct": fresh_kpis["unresolved_rate_pct"],
            "avg_resolution_hours": fresh_kpis["avg_resolution_hours"],
            "critical_unresolved_count": fresh_kpis["critical_unresolved_count"],
        },
    }


def run_api_pipeline(
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Coordinates the full REST API retrieval, cleaning, storage, and analytics refresh pipeline.
    """
    init_db(db_path)

    default_url = DEFAULT_API_URL
    default_key = DEFAULT_API_KEY

    target_url = api_url if api_url and api_url.strip() else default_url
    target_key = api_key if api_key and api_key.strip() else default_key

    # Call existing API ingestion pipeline from Module 6
    api_result = ingest_api_pipeline(
        api_url=target_url,
        api_key=target_key,
        db_path=db_path
    )

    if not api_result["success"]:
        return {
            "success": False,
            "message": api_result.get("error", "API Ingestion failed."),
            "stage_failed": api_result.get("stage_failed", "api_retrieval"),
            "data_quality": {},
            "database": {
                "records_inserted": 0,
                "records_skipped_duplicate": 0,
                "total_in_db": get_ticket_count(db_path),
            },
            "updated_kpis": None,
        }

    fresh_kpis = get_all_analytics_kpis(db_path=db_path)
    dq = api_result["dq_report"]

    return {
        "success": True,
        "message": f"Successfully ingested {api_result['inserted_count']} records from REST API ({api_result['skipped_count']} duplicate(s) skipped).",
        "stage_completed": "storage_and_analytics",
        "source_type": api_result["api_result"].source_type,
        "records_fetched": api_result["api_result"].record_count,
        "data_quality": dq.to_dict() if dq else {},
        "database": {
            "records_inserted": api_result["inserted_count"],
            "records_skipped_duplicate": api_result["skipped_count"],
            "total_in_db": get_ticket_count(db_path),
        },
        "updated_kpis": {
            "total_tickets": fresh_kpis["total_tickets"],
            "open_tickets": fresh_kpis["open_tickets"],
            "unresolved_tickets": fresh_kpis["unresolved_tickets"],
            "unresolved_rate_pct": fresh_kpis["unresolved_rate_pct"],
            "avg_resolution_hours": fresh_kpis["avg_resolution_hours"],
            "critical_unresolved_count": fresh_kpis["critical_unresolved_count"],
        },
    }


def run_full_pipeline_cycle(
    csv_path: Union[str, Path],
    db_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Executes and verifies the full workflow from CSV ingestion through
    cleaning, storage, analytics calculation, and GenAI report generation.
    """
    csv_outcome = run_csv_pipeline(csv_path, source_name="full_cycle_test", db_path=db_path)
    if not csv_outcome["success"]:
        return csv_outcome

    report_res: GenAIReportResult = generate_support_insights_report(db_path=db_path)

    return {
        "success": True,
        "pipeline_outcome": csv_outcome,
        "report": {
            "content": report_res.content,
            "is_fallback": report_res.is_fallback,
            "model_name": report_res.model_name,
            "disclaimer": report_res.disclaimer,
            "generation_time_seconds": report_res.generation_time_seconds,
        },
    }
