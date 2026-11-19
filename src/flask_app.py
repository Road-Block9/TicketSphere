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
import hmac
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
from werkzeug.exceptions import RequestEntityTooLarge

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# Re-use existing validated pipeline modules from Modules 1-7
from src.database import init_db, get_all_tickets, get_ticket_count, insert_tickets, reset_demo_data
from src.ingestion import read_csv_tickets
from src.transformation import clean_and_transform_tickets
from src.analytics import get_all_analytics_kpis
from src.api_client import ingest_api_pipeline, validate_api_url, DEFAULT_API_URL
from src.genai_assistant import generate_support_insights_report

app = Flask(__name__)

# Configure Trusted CORS Origins (replaces wildcard CORS)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

def get_allowed_cors_origins() -> list:
    custom_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if custom_env:
        custom_origins = [o.strip() for o in custom_env.split(",") if o.strip()]
        return list(dict.fromkeys(DEFAULT_CORS_ORIGINS + custom_origins))
    return DEFAULT_CORS_ORIGINS

allowed_cors_origins = get_allowed_cors_origins()
CORS(app, resources={r"/api/*": {"origins": allowed_cors_origins}})

# File Upload Limit Configuration (Default 16 MB, configurable via MAX_UPLOAD_SIZE_BYTES)
DEFAULT_MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16 MB
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", DEFAULT_MAX_UPLOAD_SIZE))

@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    max_mb = app.config.get("MAX_CONTENT_LENGTH", DEFAULT_MAX_UPLOAD_SIZE) / (1024 * 1024)
    return jsonify({
        "status": "error",
        "message": f"Uploaded file exceeds the maximum allowed size limit of {max_mb:.0f} MB.",
        "errors": [f"File size exceeds the {max_mb:.0f} MB upload limit."]
    }), 413

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

        if status_filter:
            status_filter = status_filter.strip()
        if category_filter:
            category_filter = category_filter.strip()
        if priority_filter:
            priority_filter = priority_filter.strip()

        db_path = app.config.get("DATABASE_PATH")
        # Retrieve all tickets so search and filtering are never prematurely truncated
        df = get_all_tickets(db_path=db_path)

        if not df.empty:
            # Clean and sanitize search query (strip quotes, whitespace, commas, backticks)
            clean_search = None
            if search_query:
                clean_search = search_query.strip().strip("'\"`,;\r\n").strip().lower()

            if clean_search:
                t_id_match = df["ticket_id"].astype(str).str.strip().str.lower().str.contains(clean_search, na=False)
                subj_match = df["subject"].astype(str).str.lower().str.contains(clean_search, na=False)
                desc_match = df["description"].astype(str).str.lower().str.contains(clean_search, na=False)
                cust_match = df["customer_id"].astype(str).str.strip().str.lower().str.contains(clean_search, na=False)
                cat_match = df["category"].astype(str).str.lower().str.contains(clean_search, na=False)

                search_matches = t_id_match | subj_match | desc_match | cust_match | cat_match
                filtered_df = df[search_matches]

                # If user searched directly for a ticket ID, do not let incompatible dropdown filters wipe out the ticket
                is_direct_id_search = t_id_match.any()

                if status_filter:
                    s_mask = filtered_df["status"].astype(str).str.strip().str.lower() == status_filter.lower()
                    if not is_direct_id_search or s_mask.any():
                        filtered_df = filtered_df[s_mask]

                if category_filter:
                    cat_lower = category_filter.lower()
                    c_mask = (
                        (filtered_df["category"].astype(str).str.strip().str.lower() == cat_lower) |
                        (filtered_df["category"].astype(str).str.lower().str.contains(cat_lower, na=False))
                    )
                    if not is_direct_id_search or c_mask.any():
                        filtered_df = filtered_df[c_mask]

                if priority_filter:
                    p_mask = filtered_df["priority"].astype(str).str.strip().str.lower() == priority_filter.lower()
                    if not is_direct_id_search or p_mask.any():
                        filtered_df = filtered_df[p_mask]

                df = filtered_df
            else:
                if status_filter:
                    df = df[df["status"].astype(str).str.strip().str.lower() == status_filter.lower()]
                if category_filter:
                    cat_lower = category_filter.lower()
                    df = df[
                        (df["category"].astype(str).str.strip().str.lower() == cat_lower) |
                        (df["category"].astype(str).str.lower().str.contains(cat_lower, na=False))
                    ]
                if priority_filter:
                    df = df[df["priority"].astype(str).str.strip().str.lower() == priority_filter.lower()]

            if limit:
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

    except RequestEntityTooLarge:
        raise
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error during CSV processing: {str(e)}"}), 500


@app.route("/api/ingest/api", methods=["POST"])
def ingest_api():
    """Fetches tickets from the REST API endpoint and routes through the pipeline with SSRF validation."""
    try:
        payload = request.get_json(silent=True) or {}
        api_url = payload.get("api_url")
        api_key = payload.get("api_key")

        target_url = api_url.strip() if (api_url and isinstance(api_url, str) and api_url.strip()) else DEFAULT_API_URL

        # Validate target URL against SSRF before triggering request
        is_valid, validation_err = validate_api_url(target_url)
        if not is_valid:
            return jsonify({
                "status": "error",
                "message": f"Disallowed or invalid API endpoint URL: {validation_err}",
                "stage_failed": "api_retrieval"
            }), 400

        res = run_api_pipeline(api_url=target_url, api_key=api_key)
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


def is_demo_reset_enabled() -> bool:
    """Checks whether the demo reset endpoint is permitted."""
    if "ENABLE_DEMO_RESET" in app.config:
        val = app.config["ENABLE_DEMO_RESET"]
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("true", "1", "yes")
    return os.getenv("ENABLE_DEMO_RESET", "false").lower() in ("true", "1", "yes")


@app.route("/api/demo/reset", methods=["POST"])
def reset_demo():
    """
    Safely and transactionally resets demo ticket data and ingestion logs in SQLite.
    Restores the database to a clean demo baseline so CSV and API ingestions can be demonstrated fresh.
    Protected by ENABLE_DEMO_RESET (disabled by default) and optional DEMO_RESET_TOKEN authorization.
    """
    try:
        # 1. Enforce feature toggle: disabled by default
        if not is_demo_reset_enabled():
            return jsonify({
                "status": "error",
                "message": (
                    "Demo data reset is disabled on this server. "
                    "To enable it for local demonstrations, set ENABLE_DEMO_RESET=true in your environment."
                )
            }), 403

        # 2. Check authorization token if DEMO_RESET_TOKEN is configured
        expected_token = app.config.get(
            "DEMO_RESET_TOKEN",
            os.getenv("DEMO_RESET_TOKEN", "")
        )
        if isinstance(expected_token, str):
            expected_token = expected_token.strip()
        else:
            expected_token = str(expected_token).strip()

        if expected_token:
            auth_header = request.headers.get("Authorization", "").strip()
            bearer_token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
            custom_header_token = request.headers.get("X-Reset-Token", "").strip()
            payload = request.get_json(silent=True) or {}
            body_token = payload.get("reset_token", "").strip() if isinstance(payload, dict) else ""

            provided_token = custom_header_token or bearer_token or body_token
            if not provided_token or not hmac.compare_digest(provided_token, expected_token):
                return jsonify({
                    "status": "error",
                    "message": "Unauthorized: Invalid or missing demo reset authorization token."
                }), 401

        db_path = app.config.get("DATABASE_PATH")
        res = reset_demo_data(db_path=db_path)
        return jsonify({
            "status": "success",
            "message": res["message"],
            "data": res
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to reset demo data: {str(e)}"
        }), 500



def run_flask(port: int = 5000, host: str = "127.0.0.1", debug: Optional[bool] = None):
    """Runs the Flask development server with debug mode disabled by default."""
    if debug is None:
        debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    print(f"Starting Flask Backend API on http://{host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug, use_reloader=debug)


if __name__ == "__main__":
    run_flask()
