"""
Flask Backend REST API
Module 8: React Frontend and Flask API Foundation

Provides RESTful endpoints connecting the React frontend to the existing Python modules:
- GET /api/health: System health and backend status
- GET /api/analytics/kpis: Verified SQL analytics and aggregated business metrics
- GET /api/tickets: Stored ticket records with filtering and pagination
- POST /api/ingest/csv: File upload handler routing through existing validation & transformation
- POST /api/ingest/api: Triggers API data ingestion pipeline
- POST /api/ai/report: Generates grounded GenAI management reports with honest fallback
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# Re-use existing validated pipeline modules from Modules 1-7
from src.database import init_db, get_all_tickets, get_ticket_count, insert_tickets
from src.ingestion import read_csv_tickets
from src.transformation import clean_and_transform_tickets
from src.analytics import get_all_analytics_kpis
from src.api_client import ingest_api_pipeline
from src.genai_assistant import generate_support_insights_report

app = Flask(__name__)
# Enable CORS for local Vite development (port 5173 / localhost)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Ensure DB schema is initialized on startup
init_db()


def df_to_records(df: Any) -> list:
    """Helper to convert pandas DataFrame to JSON-serializable list of records."""
    if isinstance(df, pd.DataFrame) and not df.empty:
        # Fill NaN with None for valid JSON serialization
        return df.where(pd.notna(df), None).to_dict(orient="records")
    return []


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint for frontend connection verification."""
    return jsonify({
        "status": "healthy",
        "service": "Customer Support Analytics Flask API",
        "database_connected": True,
        "total_tickets_in_db": get_ticket_count(),
        "version": "1.0.0"
    }), 200


@app.route("/api/analytics/kpis", methods=["GET"])
def get_kpis():
    """Returns verified SQL analytics and metrics aggregated in Module 5, with optional query filters."""
    try:
        start_date = request.args.get("start_date", default=None, type=str)
        end_date = request.args.get("end_date", default=None, type=str)
        category = request.args.get("category", default=None, type=str)
        priority = request.args.get("priority", default=None, type=str)

        raw_kpis = get_all_analytics_kpis(
            start_date=start_date,
            end_date=end_date,
            category=category,
            priority=priority
        )

        # Serialize DataFrames into clean JSON lists
        res_metrics = raw_kpis.get("resolution_metrics", {})
        by_cat_df = res_metrics.get("by_category_df", pd.DataFrame())

        response_payload = {
            "total_tickets": raw_kpis["total_tickets"],
            "open_tickets": raw_kpis["open_tickets"],
            "pending_tickets": raw_kpis["pending_tickets"],
            "resolved_tickets": raw_kpis["resolved_tickets"],
            "closed_tickets": raw_kpis["closed_tickets"],
            "unresolved_tickets": raw_kpis["unresolved_tickets"],
            "unresolved_rate_pct": raw_kpis["unresolved_rate_pct"],
            "avg_resolution_hours": raw_kpis["avg_resolution_hours"],
            "critical_unresolved_count": raw_kpis["critical_unresolved_count"],
            "high_unresolved_count": raw_kpis["high_unresolved_count"],
            "category_distribution": df_to_records(raw_kpis["category_distribution"]),
            "status_distribution": df_to_records(raw_kpis["status_distribution"]),
            "unresolved_by_category": df_to_records(raw_kpis["unresolved_by_category"]),
            "volume_trends": df_to_records(raw_kpis["volume_trends"]),
            "management_attention_tickets": df_to_records(raw_kpis["management_attention_tickets"]),
            "resolution_by_category": df_to_records(by_cat_df)
        }
        return jsonify({"status": "success", "data": response_payload}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to calculate analytics: {str(e)}"}), 500


@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    """Retrieves tickets from SQLite with optional filtering."""
    try:
        limit = request.args.get("limit", default=100, type=int)
        status_filter = request.args.get("status", default=None, type=str)
        category_filter = request.args.get("category", default=None, type=str)
        priority_filter = request.args.get("priority", default=None, type=str)
        search_query = request.args.get("search", default=None, type=str)

        df = get_all_tickets(limit=500)

        if not df.empty:
            if status_filter:
                df = df[df["status"].str.lower() == status_filter.lower()]
            if category_filter:
                cat_lower = category_filter.lower()
                df = df[
                    (df["category"].str.lower() == cat_lower) |
                    (df["category"].str.lower().str.contains(cat_lower, na=False))
                ]
            if priority_filter:
                df = df[df["priority"].str.lower() == priority_filter.lower()]
            if search_query:
                q = search_query.lower()
                df = df[
                    df["ticket_id"].str.lower().str.contains(q, na=False) |
                    df["subject"].str.lower().str.contains(q, na=False) |
                    df["description"].str.lower().str.contains(q, na=False)
                ]

            df = df.head(limit)

        records = df_to_records(df)
        return jsonify({
            "status": "success",
            "count": len(records),
            "tickets": records
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to retrieve tickets: {str(e)}"}), 500


from src.pipeline import run_csv_pipeline, run_api_pipeline


@app.route("/api/ingest/csv", methods=["POST"])
def ingest_csv():
    """Uploads a CSV file, runs Module 2 validation, Module 3 transformation, and Module 4 storage."""
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file part in the request."}), 400

        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            return jsonify({"status": "error", "message": "No selected file."}), 400

        # Ensure stream is rewound to beginning
        if hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
        if hasattr(uploaded_file.stream, "seek"):
            try:
                uploaded_file.stream.seek(0)
            except Exception:
                pass

        db_path = app.config.get("DATABASE_PATH")
        res = run_csv_pipeline(uploaded_file.stream, source_name=uploaded_file.filename, db_path=db_path)
        if not res["success"]:
            return jsonify({
                "status": "error",
                "message": res.get("message", "CSV Ingestion validation failed."),
                "errors": res.get("errors", []),
                "warnings": res.get("warnings", [])
            }), 400

        return jsonify({
            "status": "success",
            "message": res["message"],
            "ingestion": res["ingestion"],
            "data_quality": res["data_quality"],
            "database": res["database"],
            "updated_kpis": res.get("updated_kpis")
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error during CSV processing: {str(e)}"}), 500


@app.route("/api/ingest/api", methods=["POST"])
def ingest_api():
    """Fetches tickets from the REST API endpoint and routes through the pipeline."""
    try:
        payload = request.get_json(silent=True) or {}
        api_url = payload.get("api_url")
        api_key = payload.get("api_key")

        res = run_api_pipeline(api_url=api_url, api_key=api_key)
        if not res["success"]:
            return jsonify({
                "status": "error",
                "message": res.get("message", "API Ingestion failed."),
                "stage_failed": res.get("stage_failed", "api_retrieval")
            }), 400

        return jsonify({
            "status": "success",
            "message": res["message"],
            "source_type": res.get("source_type"),
            "records_fetched": res.get("records_fetched"),
            "data_quality": res.get("data_quality"),
            "database": res.get("database"),
            "updated_kpis": res.get("updated_kpis")
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"API ingestion failed: {str(e)}"}), 500


@app.route("/api/ai/report", methods=["POST"])
def generate_report():
    """Generates an executive management insights report using GenAI or deterministic fallback."""
    try:
        report_res = generate_support_insights_report()
        return jsonify({
            "status": "success",
            "report": report_res.content,
            "is_fallback": report_res.is_fallback,
            "model_name": report_res.model_name,
            "disclaimer": report_res.disclaimer,
            "generation_time_seconds": report_res.generation_time_seconds,
            "metrics": report_res.metrics
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Report generation failed: {str(e)}"}), 500


def run_flask(port: int = 5000, host: str = "127.0.0.1", debug: bool = False):
    """Runs the Flask development server."""
    print(f"Starting Flask Backend API on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_flask(debug=True)
