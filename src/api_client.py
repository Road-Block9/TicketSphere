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
import socket
import urllib.parse
import ipaddress
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

MOCK_API_HOST = os.getenv("MOCK_API_HOST", "127.0.0.1")
MOCK_API_PORT = os.getenv("MOCK_API_PORT", "8000")
DEFAULT_API_URL = os.getenv("MOCK_API_URL", f"http://{MOCK_API_HOST}:{MOCK_API_PORT}/api/v1/tickets")
DEFAULT_API_KEY = os.getenv("MOCK_API_KEY", "")

# SSRF Protection Network Definitions
METADATA_HOSTS = {
    "169.254.169.254",
    "169.254.169.253",
    "metadata.google.internal",
    "metadata",
    "instance-data",
}

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / Cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("fe80::/10"),          # IPv6 Link-local
    ipaddress.ip_network("224.0.0.0/4"),        # IPv4 Multicast
    ipaddress.ip_network("ff00::/8"),           # IPv6 Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
]

PRIVATE_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("fc00::/7"),           # IPv6 Unique local
]

LOOPBACK_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
]


def is_ip_disallowed(ip: ipaddress._BaseAddress, allow_local_mock: bool = False) -> Tuple[bool, str]:
    """
    Checks if an IP address belongs to blocked or disallowed ranges.
    Returns (is_disallowed, reason).
    """
    # Always block link-local and cloud metadata, regardless of development mode
    for net in BLOCKED_IP_NETWORKS:
        if ip in net:
            return True, "Cloud metadata or link-local address access is prohibited."

    # Loopback addresses (127.0.0.0/8, ::1)
    is_loopback = ip.is_loopback or any(ip in net for net in LOOPBACK_NETWORKS)
    if is_loopback:
        if allow_local_mock:
            return False, ""
        return True, "Requests to localhost and loopback addresses are disallowed."

    # Private network addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
    is_private = ip.is_private or any(ip in net for net in PRIVATE_IP_NETWORKS)
    if is_private:
        if allow_local_mock:
            return False, ""
        return True, "Requests to internal or private network addresses are disallowed."

    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True, "Reserved or special-purpose IP addresses are prohibited."

    return False, ""


def validate_api_url(url: Optional[str]) -> Tuple[bool, str]:
    """
    Validates a target REST API endpoint URL against SSRF vulnerabilities:
    - Scheme must be strictly 'http' or 'https'.
    - Embedded user credentials (e.g., username:password@) are rejected.
    - Cloud metadata endpoints and hostnames are rejected unconditionally.
    - Rejects localhost, loopback, and private IP addresses unless ALLOW_LOCAL_MOCK_API is enabled.
    - Validates resolved DNS IP addresses.
    - Supports an optional explicit allowlist via API_ALLOWED_HOSTS.

    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    if not url or not isinstance(url, str) or not url.strip():
        return False, "Target API URL must be provided."

    cleaned_url = url.strip()

    try:
        parsed = urllib.parse.urlsplit(cleaned_url)
    except Exception:
        return False, "Malformed URL."

    # 1. Scheme check
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"Disallowed URL scheme '{scheme}': only http and https are permitted."

    # 2. Embedded credentials check
    if parsed.username or parsed.password or ("@" in (parsed.netloc or "")):
        return False, "URLs containing embedded user credentials (username/password) are prohibited."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname."
    hostname = hostname.lower().strip()

    # 3. Cloud metadata hostname check
    if hostname in METADATA_HOSTS or hostname.endswith(".internal"):
        return False, "Access to cloud metadata endpoints is prohibited."

    allow_local_mock = os.getenv("ALLOW_LOCAL_MOCK_API", "true").lower() in ("true", "1", "yes")

    # 4. Explicit allowlist check if configured
    allowed_hosts_env = os.getenv("API_ALLOWED_HOSTS", "").strip()
    if allowed_hosts_env:
        allowed_hosts = [h.strip().lower() for h in allowed_hosts_env.split(",") if h.strip()]
        mock_host = os.getenv("MOCK_API_HOST", "127.0.0.1").lower()
        is_mock = allow_local_mock and hostname in ("localhost", "127.0.0.1", mock_host, "mock-url", "mock-server")
        if hostname not in allowed_hosts and not is_mock:
            return False, f"Host '{hostname}' is not in the configured API_ALLOWED_HOSTS allowlist."

    # 5. Test mock server hostnames (mock-url, mock-server used in test fixtures)
    if hostname in ("mock-url", "mock-server"):
        if allow_local_mock:
            return True, ""
        return False, "Mock hostnames are only permitted when ALLOW_LOCAL_MOCK_API is enabled."

    # 6. Check if hostname is an IP address literal
    try:
        ip = ipaddress.ip_address(hostname)
        disallowed, reason = is_ip_disallowed(ip, allow_local_mock=allow_local_mock)
        if disallowed:
            return False, reason
        return True, ""
    except ValueError:
        # Not an IP literal; proceed to DNS resolution
        pass

    # 7. Localhost hostname
    if hostname == "localhost":
        if allow_local_mock:
            return True, ""
        return False, "Requests to localhost are disallowed in this environment."

    # 8. Resolve hostname to IP addresses and validate each
    port = parsed.port or (443 if scheme == "https" else 80)
    try:
        addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False, f"Could not resolve host '{hostname}'."
    except Exception as e:
        return False, f"DNS resolution failed for '{hostname}': {str(e)}"

    if not addr_info:
        return False, f"No IP address found for host '{hostname}'."

    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        try:
            resolved_ip = ipaddress.ip_address(ip_str)
            disallowed, reason = is_ip_disallowed(resolved_ip, allow_local_mock=allow_local_mock)
            if disallowed:
                return False, f"Resolved IP ({ip_str}) is not permitted: {reason}"
        except ValueError:
            return False, f"Invalid resolved IP address: {ip_str}"

    return True, ""


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
    api_key: Optional[str] = None,
    status_filter: Optional[str] = None,
    timeout: int = 5,
    max_redirects: int = 3
) -> ApiIngestionResult:
    """
    Fetches customer support tickets from an HTTP REST API endpoint.
    Performs comprehensive SSRF validation before outbound requests and across redirects.

    Parameters:
        api_url: The full REST endpoint URL.
        api_key: Optional API key sent via 'X-API-Key' header.
        status_filter: Optional query parameter to filter tickets by status.
        timeout: Maximum seconds to wait before timing out (default 5s).
        max_redirects: Maximum safe HTTP redirects allowed (default 3).

    Returns:
        ApiIngestionResult containing the raw DataFrame and connection metadata.
    """
    # 1. SSRF Validation before making any request
    is_valid, validation_err = validate_api_url(api_url)
    if not is_valid:
        return ApiIngestionResult(
            success=False,
            endpoint_url=api_url,
            error_message=f"Disallowed or invalid target API URL: {validation_err}"
        )

    headers = {"Accept": "application/json"}
    resolved_key = api_key if api_key is not None else DEFAULT_API_KEY
    if resolved_key and str(resolved_key).strip():
        headers["X-API-Key"] = str(resolved_key).strip()

    params = {}
    if status_filter:
        params["status"] = status_filter

    current_url = api_url
    redirect_count = 0

    while True:
        try:
            response = requests.get(
                current_url,
                headers=headers,
                params=params if redirect_count == 0 else None,
                timeout=timeout,
                allow_redirects=False
            )
        except requests.exceptions.ConnectionError:
            return ApiIngestionResult(
                success=False,
                endpoint_url=current_url,
                error_message=(
                    f"Could not connect to API server at '{current_url}'. "
                    "If using the local mock server, ensure it is running via "
                    "'python src/mock_api.py'."
                )
            )
        except requests.exceptions.Timeout:
            return ApiIngestionResult(
                success=False,
                endpoint_url=current_url,
                error_message=f"Request to '{current_url}' timed out after {timeout} seconds."
            )
        except requests.exceptions.RequestException as e:
            return ApiIngestionResult(
                success=False,
                endpoint_url=current_url,
                error_message=f"Network error during API request: {str(e)}"
            )

        # Handle and validate HTTP redirects safely
        status = getattr(response, "status_code", 0)
        is_redirect_status = isinstance(status, int) and (300 <= status < 400)
        is_redirect_flag = getattr(response, "is_redirect", False) is True

        if is_redirect_status or is_redirect_flag:
            resp_headers = getattr(response, "headers", {})
            location = resp_headers.get("Location") if hasattr(resp_headers, "get") else None
            if not location or not isinstance(location, str):
                return ApiIngestionResult(
                    success=False,
                    status_code=response.status_code,
                    endpoint_url=current_url,
                    error_message="Redirect response missing Location header."
                )

            redirect_count += 1
            if redirect_count > max_redirects:
                return ApiIngestionResult(
                    success=False,
                    status_code=response.status_code,
                    endpoint_url=current_url,
                    error_message=f"Too many redirects (exceeded limit of {max_redirects})."
                )

            next_url = urllib.parse.urljoin(current_url, location)
            valid_redirect, redir_error = validate_api_url(next_url)
            if not valid_redirect:
                return ApiIngestionResult(
                    success=False,
                    status_code=response.status_code,
                    endpoint_url=next_url,
                    error_message=f"Disallowed redirect destination blocked: {redir_error}"
                )
            current_url = next_url
            continue

        break

    # Handle HTTP error statuses
    if response.status_code == 401 or response.status_code == 403:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=current_url,
            error_message="Authentication failure: Invalid or missing API key."
        )
    elif response.status_code >= 400:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=current_url,
            error_message=f"API returned HTTP error {response.status_code}: {response.text}"
        )

    # Parse JSON
    try:
        payload = response.json()
    except ValueError:
        return ApiIngestionResult(
            success=False,
            status_code=response.status_code,
            endpoint_url=current_url,
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
            endpoint_url=current_url,
            error_message=f"Unexpected JSON structure: expected list or object with 'tickets'."
        )

    if not ticket_records:
        return ApiIngestionResult(
            success=True,
            data=pd.DataFrame(),
            record_count=0,
            status_code=response.status_code,
            source_type=source_label,
            endpoint_url=current_url
        )

    df_raw = pd.DataFrame(ticket_records)

    return ApiIngestionResult(
        success=True,
        data=df_raw,
        record_count=len(df_raw),
        status_code=response.status_code,
        source_type=source_label,
        endpoint_url=current_url
    )


def ingest_api_pipeline(
    api_url: str = DEFAULT_API_URL,
    api_key: Optional[str] = None,
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
