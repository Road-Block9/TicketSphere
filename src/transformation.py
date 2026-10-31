"""
Data Cleaning and Transformation Module
Module 3: Customer Support Ticket Analytics & GenAI Business Assistant

Transforms raw customer support ticket data into reliable, analysis-ready records:
- Deduplicates ticket records based on ticket_id
- Cleans whitespace and normalises status, category, and priority values
- Validates and parses timestamps into standard ISO-8601 format
- Calculates operational metrics (resolution_time_hours, is_unresolved)
- Strictly prevents fabricated resolution times for unresolved tickets
- Tracks comprehensive Data Quality (DQ) metrics: accepted, corrected, and rejected records
"""

from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


# Standardised reference taxonomies
STANDARD_STATUSES = {
    "open": "Open",
    "in progress": "Pending",
    "in_progress": "Pending",
    "pending": "Pending",
    "waiting": "Pending",
    "resolved": "Resolved",
    "fixed": "Resolved",
    "closed": "Closed",
    "completed": "Closed",
}

STANDARD_CATEGORIES = {
    "delivery & shipping": "Delivery & Shipping",
    "delivery": "Delivery & Shipping",
    "shipping": "Delivery & Shipping",
    "logistics": "Delivery & Shipping",
    "billing & refunds": "Billing & Refunds",
    "billing": "Billing & Refunds",
    "refund": "Billing & Refunds",
    "refunds": "Billing & Refunds",
    "payment": "Billing & Refunds",
    "payments": "Billing & Refunds",
    "product quality": "Product Quality",
    "product": "Product Quality",
    "quality": "Product Quality",
    "hardware": "Product Quality",
    "defect": "Product Quality",
    "technical support": "Technical Support",
    "technical": "Technical Support",
    "tech": "Technical Support",
    "tech support": "Technical Support",
    "software": "Technical Support",
    "customer service": "Customer Service",
    "service": "Customer Service",
    "support": "Customer Service",
    "feedback": "Customer Service",
}

STANDARD_PRIORITIES = {
    "critical": "Critical",
    "urgent": "Critical",
    "high": "High",
    "medium": "Medium",
    "normal": "Medium",
    "low": "Low",
    "minor": "Low",
}


@dataclass
class DataQualityReport:
    """Tracks record counts, corrections, imputations, and rejections."""
    total_received: int = 0
    accepted: int = 0
    corrected: int = 0
    rejected: int = 0
    duplicates_dropped: int = 0
    imputed_fields: Dict[str, int] = field(default_factory=dict)
    date_anomalies: int = 0
    rejection_log: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> str:
        """Generates a formatted ASCII data quality audit report."""
        lines = [
            "=" * 65,
            "DATA QUALITY & TRANSFORMATION AUDIT REPORT",
            "=" * 65,
            f"Total Records Received : {self.total_received}",
            f"Accepted for Storage   : {self.accepted}",
            f"Corrected / Imputed    : {self.corrected}",
            f"Rejected Records       : {self.rejected}",
            f"Duplicates Removed     : {self.duplicates_dropped}",
            f"Date Anomalies         : {self.date_anomalies}",
        ]
        if self.imputed_fields:
            lines.append("-" * 65)
            lines.append("Imputed / Standardised Fields:")
            for field_name, count in self.imputed_fields.items():
                lines.append(f"  • {field_name:<24} : {count} occurrences")
        if self.rejection_log:
            lines.append("-" * 65)
            lines.append("Rejection Log:")
            for item in self.rejection_log:
                lines.append(f"  • Ticket '{item.get('ticket_id', 'UNKNOWN')}': {item.get('reason')}")
        lines.append("=" * 65)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Returns the report as a dictionary for Streamlit or API serialization."""
        return {
            "total_received": self.total_received,
            "accepted": self.accepted,
            "corrected": self.corrected,
            "rejected": self.rejected,
            "duplicates_dropped": self.duplicates_dropped,
            "imputed_fields": self.imputed_fields,
            "date_anomalies": self.date_anomalies,
            "rejection_log": self.rejection_log,
        }


def clean_and_transform_tickets(
    df_raw: pd.DataFrame
) -> Tuple[pd.DataFrame, DataQualityReport]:
    """
    Cleans raw ticket data, enforces integrity rules, standardises values,
    computes resolution metrics, and returns clean records with a DQ report.
    """
    report = DataQualityReport()
    report.total_received = len(df_raw)

    if df_raw.empty:
        return pd.DataFrame(), report

    # Defensive copy to avoid modifying raw input
    df = df_raw.copy()

    # Step 1: Strip whitespace across all string columns
    for col in df.select_dtypes(include=["object", "string", "str"]).columns:
        df[col] = df[col].astype(str).str.strip()
        # Replace string literal representations of null
        df[col] = df[col].replace(["nan", "NaN", "None", "null", "NULL", ""], np.nan)

    # Step 2: Validate Ticket IDs & Filter Out Empty Primary Keys
    invalid_id_mask = df["ticket_id"].isna()
    if invalid_id_mask.any():
        rejected_count = int(invalid_id_mask.sum())
        report.rejected += rejected_count
        for idx in df[invalid_id_mask].index:
            report.rejection_log.append({
                "ticket_id": "MISSING",
                "reason": "Missing or null ticket_id primary key",
                "row_index": int(idx)
            })
        df = df[~invalid_id_mask].copy()

    # Step 3: Duplicate Ticket ID Detection & Removal
    initial_len = len(df)
    df = df.drop_duplicates(subset=["ticket_id"], keep="first")
    duplicates_dropped = initial_len - len(df)
    report.duplicates_dropped = duplicates_dropped
    if duplicates_dropped > 0:
        report.corrected += duplicates_dropped

    # Step 4: Validate and Standardise Created Timestamp
    # created_at is mandatory for time-series analytics
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    invalid_created_mask = df["created_at_dt"].isna()
    if invalid_created_mask.any():
        unparseable_count = int(invalid_created_mask.sum())
        report.rejected += unparseable_count
        for _, row in df[invalid_created_mask].iterrows():
            report.rejection_log.append({
                "ticket_id": str(row.get("ticket_id")),
                "reason": f"Invalid or missing creation timestamp: '{row.get('created_at')}'"
            })
        df = df[~invalid_created_mask].copy()

    if df.empty:
        report.accepted = 0
        return pd.DataFrame(), report

    # Step 5: Standardise Status
    def normalize_status(val: Any) -> str:
        if pd.isna(val):
            return "Open"
        cleaned = str(val).strip().lower()
        return STANDARD_STATUSES.get(cleaned, str(val).strip().title())

    orig_status = df["status"].copy() if "status" in df.columns else pd.Series("Open", index=df.index)
    df["status"] = orig_status.apply(normalize_status)
    status_changed = (orig_status.astype(str) != df["status"]).sum()
    if status_changed > 0:
        report.imputed_fields["status_standardised"] = int(status_changed)
        report.corrected += int(status_changed)

    # Step 6: Standardise Category
    def normalize_category(val: Any) -> str:
        if pd.isna(val):
            return "Customer Service"
        cleaned = str(val).strip().lower()
        return STANDARD_CATEGORIES.get(cleaned, str(val).strip().title())

    orig_category = df["category"].copy() if "category" in df.columns else pd.Series("Customer Service", index=df.index)
    df["category"] = orig_category.apply(normalize_category)
    category_changed = (orig_category.astype(str) != df["category"]).sum()
    if category_changed > 0:
        report.imputed_fields["category_standardised"] = int(category_changed)
        report.corrected += int(category_changed)

    # Step 7: Standardise Priority
    def normalize_priority(val: Any) -> str:
        if pd.isna(val):
            return "Medium"
        cleaned = str(val).strip().lower()
        return STANDARD_PRIORITIES.get(cleaned, "Medium")

    orig_priority = df["priority"].copy() if "priority" in df.columns else pd.Series("Medium", index=df.index)
    df["priority"] = orig_priority.apply(normalize_priority)
    priority_changed = (orig_priority.astype(str) != df["priority"]).sum()
    if priority_changed > 0:
        report.imputed_fields["priority_standardised"] = int(priority_changed)
        report.corrected += int(priority_changed)

    # Step 8: Parse and Validate Resolved Timestamp
    if "resolved_at" in df.columns:
        df["resolved_at_dt"] = pd.to_datetime(df["resolved_at"], errors="coerce")
    else:
        df["resolved_at_dt"] = pd.NaT

    # Step 9: Calculate Resolution Duration & Enforce Rules
    # Rule A: Unresolved tickets (Open/Pending) MUST NOT have a resolution date or fabricated resolution time
    unresolved_mask = df["status"].isin(["Open", "Pending"])
    
    # Check if an open/pending ticket had a resolution date populated erroneously
    false_resolution_dates = unresolved_mask & df["resolved_at_dt"].notna()
    if false_resolution_dates.any():
        anomaly_count = int(false_resolution_dates.sum())
        report.date_anomalies += anomaly_count
        report.imputed_fields["cleared_false_resolution_dates"] = anomaly_count
        report.corrected += anomaly_count
        # Clear resolution date for open/pending tickets
        df.loc[false_resolution_dates, "resolved_at_dt"] = pd.NaT

    # Rule B: Resolved/Closed tickets with resolved_at earlier than created_at (Negative duration)
    negative_duration_mask = (
        (~unresolved_mask) &
        df["resolved_at_dt"].notna() &
        (df["resolved_at_dt"] < df["created_at_dt"])
    )
    if negative_duration_mask.any():
        neg_count = int(negative_duration_mask.sum())
        report.date_anomalies += neg_count
        report.imputed_fields["negative_duration_anomalies_cleared"] = neg_count
        report.corrected += neg_count
        df.loc[negative_duration_mask, "resolved_at_dt"] = pd.NaT

    # Compute resolution_time_hours strictly for valid resolved/closed tickets
    duration_series = (df["resolved_at_dt"] - df["created_at_dt"]).dt.total_seconds() / 3600.0
    # Round to 2 decimal places, set NaN where unresolved or date missing
    df["resolution_time_hours"] = duration_series.apply(
        lambda x: round(float(x), 2) if pd.notna(x) and x >= 0 else None
    )

    # Computed flag: is_unresolved
    df["is_unresolved"] = unresolved_mask.astype(int)

    # Step 10: Standardise String Fields & Handle Missing Values
    # Customer ID
    if "customer_id" not in df.columns:
        df["customer_id"] = "CUST-UNKNOWN"
        report.imputed_fields["imputed_customer_id"] = len(df)
        report.corrected += len(df)
    elif df["customer_id"].isna().any():
        missing_cust = int(df["customer_id"].isna().sum())
        df["customer_id"] = df["customer_id"].astype(object).fillna("CUST-UNKNOWN")
        report.imputed_fields["imputed_customer_id"] = missing_cust
        report.corrected += missing_cust

    # Subject
    if "subject" not in df.columns:
        df["subject"] = "No Subject Provided"
        report.imputed_fields["imputed_subject"] = len(df)
        report.corrected += len(df)
    elif df["subject"].isna().any():
        missing_subj = int(df["subject"].isna().sum())
        df["subject"] = df["subject"].astype(object).fillna("No Subject Provided")
        report.imputed_fields["imputed_subject"] = missing_subj
        report.corrected += missing_subj

    # Description
    if "description" not in df.columns:
        df["description"] = "No Description Provided"
        report.imputed_fields["imputed_description"] = len(df)
        report.corrected += len(df)
    elif df["description"].isna().any():
        missing_desc = int(df["description"].isna().sum())
        df["description"] = df["description"].astype(object).fillna("No Description Provided")
        report.imputed_fields["imputed_description"] = missing_desc
        report.corrected += missing_desc

    # Resolution Notes
    if "resolution_notes" not in df.columns:
        df["resolution_notes"] = None
    else:
        # Fill missing notes for resolved tickets with audit note
        missing_notes_resolved = (~unresolved_mask) & df["resolution_notes"].isna()
        if missing_notes_resolved.any():
            notes_count = int(missing_notes_resolved.sum())
            df.loc[missing_notes_resolved, "resolution_notes"] = "Resolved with no notes logged."
            report.imputed_fields["imputed_resolution_notes"] = notes_count
            report.corrected += notes_count
        # Unresolved tickets keep None for resolution_notes
        df.loc[unresolved_mask, "resolution_notes"] = None

    # Step 11: Final Formatted Date Strings for SQLite Storage
    df["created_at"] = df["created_at_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["resolved_at"] = df["resolved_at_dt"].apply(
        lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else None
    )

    # Drop temporary datetime helper columns
    df = df.drop(columns=["created_at_dt", "resolved_at_dt"])

    # Final schema ordering
    ordered_columns = [
        "ticket_id",
        "customer_id",
        "created_at",
        "resolved_at",
        "category",
        "priority",
        "status",
        "subject",
        "description",
        "resolution_notes",
        "resolution_time_hours",
        "is_unresolved"
    ]
    df_clean = df[ordered_columns].copy()

    # Step 12: Record Final Metrics
    report.accepted = len(df_clean)

    return df_clean, report


if __name__ == "__main__":
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from src.ingestion import read_csv_tickets

    target_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/customer_support_tickets.csv"
    print(f"Loading raw file: {target_path}")
    ingestion_res = read_csv_tickets(target_path)

    if not ingestion_res.success or ingestion_res.data is None:
        print(f"[ERROR] Ingestion failed: {ingestion_res.errors}")
        sys.exit(1)

    print(f"Ingested {len(ingestion_res.data)} records. Running transformation pipeline...")
    cleaned_df, dq_report = clean_and_transform_tickets(ingestion_res.data)

    print(dq_report.summary())
    print("\nPreview of Cleaned Records (First 5):")
    print(cleaned_df[[
        "ticket_id", "status", "category", "priority",
        "created_at", "resolved_at", "resolution_time_hours", "is_unresolved"
    ]].head(5).to_string(index=False))
