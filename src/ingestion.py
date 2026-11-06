"""
CSV Data Ingestion Module
Module 2: Customer Support Ticket Analytics & GenAI Business Assistant

Handles ingestion of raw customer support ticket CSV data:
- Ingests from file paths (str/Path) or file buffers (Streamlit UploadedFile)
- Validates file presence, empty files, and malformed encoding
- Audits and standardises column headers
- Enforces presence of core required columns
- Preserves raw input data without destructive in-place alterations
- Generates structured ingestion audit summaries
"""

import os
import io
import re
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
from dataclasses import dataclass, field
import pandas as pd


# Core columns required for the pipeline to generate meaningful SQL analytics
REQUIRED_COLUMNS = ["ticket_id", "created_at", "status", "category"]

# Known column aliases across different CRM export schemas (Zendesk, Salesforce, Freshdesk, ExploreMyData, HowToCSV)
COLUMN_ALIASES: Dict[str, str] = {
    # ticket_id aliases
    "ticket_id": "ticket_id",
    "ticketid": "ticket_id",
    "id": "ticket_id",
    "ticket_number": "ticket_id",
    "ticket_no": "ticket_id",
    "ticket_num": "ticket_id",
    "case_id": "ticket_id",
    "case_number": "ticket_id",
    "issue_id": "ticket_id",

    # created_at aliases
    "created_at": "created_at",
    "created_date": "created_at",
    "creation_date": "created_at",
    "date_created": "created_at",
    "created": "created_at",
    "open_date": "created_at",
    "opened_at": "created_at",
    "ticket_date": "created_at",
    "date": "created_at",
    "timestamp": "created_at",

    # resolved_at aliases
    "resolved_at": "resolved_at",
    "resolved_date": "resolved_at",
    "resolution_date": "resolved_at",
    "resolution_time": "resolved_at",
    "time_to_resolution": "resolved_at",
    "closed_at": "resolved_at",
    "closed_date": "resolved_at",
    "date_resolved": "resolved_at",
    "resolved": "resolved_at",

    # status aliases
    "status": "status",
    "ticket_status": "status",
    "state": "status",
    "case_status": "status",
    "issue_status": "status",
    "current_status": "status",

    # category aliases
    "category": "category",
    "ticket_category": "category",
    "ticket_type": "category",
    "issue_type": "category",
    "type": "category",
    "complaint_category": "category",
    "issue_category": "category",
    "case_type": "category",

    # priority aliases
    "priority": "priority",
    "ticket_priority": "priority",
    "urgency": "priority",
    "severity": "priority",
    "priority_level": "priority",

    # customer_id aliases
    "customer_id": "customer_id",
    "customerid": "customer_id",
    "client_id": "customer_id",
    "user_id": "customer_id",
    "account_id": "customer_id",
    "requester_id": "customer_id",

    # subject aliases
    "subject": "subject",
    "ticket_subject": "subject",
    "title": "subject",
    "issue_title": "subject",
    "summary": "subject",

    # description aliases
    "description": "description",
    "ticket_description": "description",
    "details": "description",
    "issue_description": "description",
    "notes": "description",
    "body": "description",

    # resolution_notes aliases
    "resolution_notes": "resolution_notes",
    "resolution": "resolution_notes",
    "solution": "resolution_notes",
    "closing_notes": "resolution_notes",
    "resolution_comment": "resolution_notes",
}


@dataclass
class IngestionResult:
    """Standardised result container for data ingestion operations."""
    success: bool
    data: Optional[pd.DataFrame] = None
    record_count: int = 0
    columns_found: List[str] = field(default_factory=list)
    missing_required_columns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Returns a formatted human-readable summary of the ingestion audit."""
        lines = [
            "=" * 60,
            "CSV INGESTION AUDIT REPORT",
            "=" * 60,
            f"Status       : {'SUCCESS' if self.success else 'FAILED'}",
            f"Record Count : {self.record_count}",
            f"Columns Found: {len(self.columns_found)} ({', '.join(self.columns_found) if self.columns_found else 'None'})",
        ]
        if self.missing_required_columns:
            lines.append(f"Missing Reqd : {', '.join(self.missing_required_columns)}")
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  • {w}")
        if self.errors:
            lines.append("Errors:")
            for e in self.errors:
                lines.append(f"  • {e}")
        lines.append("=" * 60)
        return "\n".join(lines)


def normalize_column_name(col: str) -> str:
    """
    Normalizes a raw column header to lowercase snake_case and resolves known aliases:
    - Strips UTF-8 BOM, surrounding quotes, and whitespace.
    - Replaces consecutive spaces, hyphens, dots, and slashes with an underscore.
    - Resolves known CRM/helpdesk aliases into canonical names.
    """
    raw = str(col).strip().lstrip("\ufeff").strip("\"' ")
    clean = re.sub(r"[\s\-\./]+", "_", raw.lower())
    clean = re.sub(r"[^\w]", "", clean).strip("_")
    return COLUMN_ALIASES.get(clean, clean)


def read_csv_tickets(
    file_source: Union[str, Path, io.BytesIO, io.StringIO, Any],
    encoding: str = "utf-8"
) -> IngestionResult:
    """
    Ingests and validates customer support ticket data from a CSV source.

    Parameters:
        file_source: Path to CSV file, or a file-like buffer (e.g. Streamlit UploadedFile)
        encoding: File character encoding (defaults to 'utf-8')

    Returns:
        IngestionResult with validation metrics and raw DataFrame.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Validate File Existence and Non-Empty Size (for file paths)
    if isinstance(file_source, (str, Path)):
        path_obj = Path(file_source)
        if not path_obj.exists():
            errors.append(f"File not found: {path_obj.resolve()}")
            return IngestionResult(success=False, errors=errors)

        try:
            file_size = path_obj.stat().st_size
            if file_size == 0:
                errors.append(f"The file '{path_obj.name}' is empty (0 bytes).")
                return IngestionResult(success=False, errors=errors)
        except OSError as e:
            errors.append(f"Failed to access file '{path_obj}': {str(e)}")
            return IngestionResult(success=False, errors=errors)

    # 2. Validate Buffer Size (for Streamlit UploadedFile / BytesIO / StringIO / FileStorage)
    elif hasattr(file_source, "size") and getattr(file_source, "size") == 0:
        errors.append("Uploaded file buffer is empty (0 bytes).")
        return IngestionResult(success=False, errors=errors)
    elif hasattr(file_source, "content_length") and getattr(file_source, "content_length") == 0:
        errors.append("Uploaded file buffer is empty (0 bytes).")
        return IngestionResult(success=False, errors=errors)

    # 3. Read CSV into Pandas with error handling
    try:
        # If wrapped stream or FileStorage, ensure seek to beginning
        if hasattr(file_source, "stream") and hasattr(file_source.stream, "seek"):
            try:
                file_source.stream.seek(0)
            except Exception:
                pass
        if hasattr(file_source, "seek"):
            try:
                file_source.seek(0)
            except Exception:
                pass

        # Use utf-8-sig to automatically handle standard utf-8 and optional BOM headers
        effective_encoding = "utf-8-sig" if encoding.lower() in ("utf-8", "utf8", "utf-8-sig") else encoding
        df_raw = pd.read_csv(file_source, encoding=effective_encoding)

    except pd.errors.EmptyDataError:
        errors.append("File contains no data or empty header line.")
        return IngestionResult(success=False, errors=errors)

    except pd.errors.ParserError as pe:
        errors.append(f"Malformed CSV structure. Parsing error: {str(pe)}")
        return IngestionResult(success=False, errors=errors)

    except UnicodeDecodeError:
        # Attempt fallback to latin-1 encoding
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            df_raw = pd.read_csv(file_source, encoding="latin-1")
            warnings.append("File was encoded in Latin-1; standard UTF-8 recommended.")
        except Exception as fallback_err:
            errors.append(f"Character encoding failure: {str(fallback_err)}")
            return IngestionResult(success=False, errors=errors)

    except Exception as general_err:
        errors.append(f"Unexpected error while reading CSV: {str(general_err)}")
        return IngestionResult(success=False, errors=errors)

    # 4. Check for Empty Rows / 0 records
    if df_raw.empty:
        errors.append("CSV file contains valid headers, but zero data records.")
        return IngestionResult(
            success=False,
            data=df_raw,
            columns_found=list(df_raw.columns),
            errors=errors
        )

    # 5. Column Standardisation & Schema Check
    original_columns = list(df_raw.columns)
    mapped_columns = [normalize_column_name(c) for c in original_columns]
    
    # Check for rename changes
    renamed_count = sum(1 for orig, mapped in zip(original_columns, mapped_columns) if orig != mapped)
    if renamed_count > 0:
        warnings.append(f"Normalized {renamed_count} column header(s) to standard naming format.")

    # Apply normalised column names to a working copy (preserve original columns in result)
    df_ingested = df_raw.copy()
    df_ingested.columns = mapped_columns

    # 6. Verify Core Required Columns
    missing_required = [req for req in REQUIRED_COLUMNS if req not in df_ingested.columns]

    if missing_required:
        errors.append(
            f"Missing required column(s): {', '.join(missing_required)}. "
            f"Expected minimum schema: {', '.join(REQUIRED_COLUMNS)}."
        )
        return IngestionResult(
            success=False,
            data=df_ingested,
            record_count=len(df_ingested),
            columns_found=mapped_columns,
            missing_required_columns=missing_required,
            errors=errors,
            warnings=warnings
        )

    # 7. Success
    return IngestionResult(
        success=True,
        data=df_ingested,
        record_count=len(df_ingested),
        columns_found=mapped_columns,
        missing_required_columns=[],
        errors=[],
        warnings=warnings
    )


if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else "data/raw/customer_support_tickets.csv"
    print(f"Testing CSV ingestion on: {test_file}")
    res = read_csv_tickets(test_file)
    print(res.summary())
    if res.success and res.data is not None:
        print("\nFirst 3 records preview:")
        print(res.data.head(3).to_string(index=False))
