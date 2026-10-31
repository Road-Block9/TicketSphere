"""
API Data Ingestion Client Module
Module 6: Customer Support Ticket Analytics & GenAI Business Assistant

Connects to REST APIs (external or local simulated server) to ingest ticket records:
- Sends HTTP requests with configurable timeouts and authentication headers
- Handles network errors, timeouts, HTTP 4xx/5xx, and malformed responses gracefully
- Parses JSON payloads into analysis-ready pandas DataFrames
- Routes ingested data through the existing transformation (Module 3) and database (Module 4) pipelines
- Clearly distinguishes between real external API data and simulated mock API demonstration data
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import requests
import pandas as pd
from dotenv import load_dotenv

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.transformation import clean_and_transform_tickets, DataQualityReport
from src.database import insert_tickets, init_db, get_db_path

DEFAULT_API_URL = os.getenv("MOCK_API_URL", "http://127.0.0.1:8000/api/v1/tickets")
DEFAULT_API_KEY = os.getenv("MOCK_API_KEY", "capstone-demo-key-2026")


@dataclass
class ApiIngestionResult:
    """Container for API fetch and ingestion status."""
    success: bool
    data: Optional[pd.DataFrame] = None
    record_count: int = 0
    status_code: Optional[int] = None
    source_type: str = "SIMULATED_MOCK_API"
    error_message: Optional[str] = None
    endpoint_url: str = ""

    def summary(self) -> str:
        """Returns a formatted summary of the API ingestion."""
        lines = [
            "=" * 60,
            "API DATA INGESTION REPORT",
            "=" * 60,
            f"Endpoint URL  : {self.endpoint_url}",
            f"Data Source   : {self.source_type}",
            f"HTTP Status   : {self.status_code if self.status_code else 'N/A'}",
            f"Success       : {self.success}",
            f"Records Found : {self.record_count}",
        ]
        if self.error_message:
            lines.append(f"Error Details : {self.error_message}")
        lines.append("=" * 60)
        return "\n".join(lines)


def fetch_tickets_from_api(
    api_url: str = DEFAULT_API_URL,
    api_key: Optional[str] = DEFAULT_API_KEY,
    status_filter: Optional[str] = None,
    timeout: int = 5
) -> ApiIngestionResult:
    """
    Fetches customer support tickets from an HTTP REST API endpoint.

    Parameters:
        api_url: The full REST endpoint URL.
        api_key: Optional API key sent via 'X-API-Key' header.
        status_filter: Optional query parameter to filter tickets by status.
        timeout: Maximum seconds to wait before timing out (default 5s).

    Returns:
        ApiIngestionResult containing the raw DataFrame and connection metadata.
    """
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    params = {}
    if status_filter:
        params["status"] = status_filter

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=timeout)
    except requests.exceptions.ConnectionError:
        return ApiIngestionResult(
            success=False,
            endpoint_url=api_url,
            error_message=(
                f"Could not connect to API server at '{api_url}'. "
                "If using the local mock server, ensure it is running via "
                "'python src/mock_api.py'."
            )
        )
    except requests.exceptions.Timeout:
        return ApiIngestionResult(
            success=False,
            endpoint_url=api_url,
            error_message=f"Request to '{api_url}' timed out after {timeout} seconds."
        )
    except requests.exceptions.RequestException as e:
        return ApiIngestionResult(
            success=False,
            endpoint_url=api_url,
            error_message=f"Network error during API request: {str(e)}"
        )

    # Handle HTTP error statuses
    if response.status_code == 401 or response.status_code == 403:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=api_url,
            error_message="Authentication failure: Invalid or missing API key."
        )
    elif response.status_code >= 400:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=api_url,
            error_message=f"API returned HTTP error {response.status_code}: {response.text}"
        )

    # Parse JSON
    try:
        payload = response.json()
    except ValueError:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=api_url,
            error_message="API response was not valid JSON."
        )

    # Extract ticket list from payload (handles either list root or {"tickets": [...]})
    if isinstance(payload, list):
        ticket_records = payload
        source_label = "EXTERNAL_REST_API"
    elif isinstance(payload, dict):
        ticket_records = payload.get("tickets", [])
        source_label = payload.get("source", "SIMULATED_MOCK_API")
    else:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=api_url,
            error_message=f"Unexpected JSON structure: expected list or object with 'tickets'."
        )

    if not ticket_records:
        return ApiIngestionResult(
            success=True,
            data=pd.DataFrame(),
            record_count=0,
            status_code=response.status_code,
            source_type=source_label,
            endpoint_url=api_url
        )

    df_raw = pd.DataFrame(ticket_records)

    return ApiIngestionResult(
        success=True,
        data=df_raw,
        record_count=len(df_raw),
        status_code=response.status_code,
        source_type=source_label,
        endpoint_url=api_url
    )


def ingest_api_pipeline(
    api_url: str = DEFAULT_API_URL,
    api_key: Optional[str] = DEFAULT_API_KEY,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    End-to-end API ingestion workflow:
    1. Fetches data via HTTP from the REST API
    2. Runs data through the standard Transformation layer (Module 3)
    3. Persists records into SQLite with duplicate prevention (Module 4)

    Returns a comprehensive execution audit dictionary.
    """
    fetch_result = fetch_tickets_from_api(api_url=api_url, api_key=api_key)

    if not fetch_result.success or fetch_result.data is None:
        return {
            "success": False,
            "stage_failed": "api_fetch",
            "error": fetch_result.error_message,
            "api_result": fetch_result,
            "dq_report": None,
            "inserted_count": 0,
            "skipped_count": 0
        }

    # Pass through Module 3 transformation
    cleaned_df, dq_report = clean_and_transform_tickets(fetch_result.data)

    # Pass through Module 4 database storage
    inserted, skipped = insert_tickets(
        cleaned_df,
        db_path=db_path,
        source_name=f"api:{fetch_result.source_type.lower()}"
    )

    return {
        "success": True,
        "stage_failed": None,
        "error": None,
        "api_result": fetch_result,
        "dq_report": dq_report,
        "inserted_count": inserted,
        "skipped_count": skipped,
        "final_records": len(cleaned_df)
    }


if __name__ == "__main__":
    print("Testing API ingestion client against default endpoint:")
    print(f"Target URL: {DEFAULT_API_URL}")
    res = fetch_tickets_from_api()
    print(res.summary())
    if res.success and res.data is not None:
        print("\nFirst 3 records retrieved from API:")
        print(res.data.head(3).to_string(index=False))
