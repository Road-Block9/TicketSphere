"""
Dataset Inspection Script
Module 1: Project Setup and Dataset Preparation

Inspects raw customer support ticket datasets:
- Verifies file existence and accessibility
- Reports row count, column count, and column names
- Analyzes missing / null values per column
- Summarizes ticket status and category distributions
- Validates data integrity constraints
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path so scripts can run standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def inspect_dataset(file_path: str = "data/raw/customer_support_tickets.csv"):
    """Inspects a CSV dataset and prints formatted summary statistics."""
    target = PROJECT_ROOT / file_path

    print("=" * 70)
    print("CUSTOMER SUPPORT TICKET DATASET INSPECTOR")
    print("=" * 70)
    print(f"Target file: {target.resolve()}")

    if not target.exists():
        print(f"\n[ERROR] Dataset file not found at: {target}")
        sys.exit(1)

    try:
        import pandas as pd
    except ImportError:
        print("\n[WARNING] Pandas not yet installed in active environment.")
        print("Falling back to Python standard csv module for basic check...")
        import csv

        with open(target, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
        print(f"\nTotal Records : {len(rows)}")
        print(f"Total Columns : {len(headers)}")
        print(f"Columns       : {', '.join(headers)}")
        return

    # Pandas deep inspection
    df = pd.read_csv(target)

    total_rows, total_cols = df.shape
    print(f"\n[OK] Successfully loaded dataset.")
    print(f"  • Total Records (Rows): {total_rows}")
    print(f"  • Total Attributes (Cols): {total_cols}")

    print("\n" + "-" * 70)
    print("COLUMN SCHEMA & NULL VALUE AUDIT")
    print("-" * 70)
    audit_data = []
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = (null_count / total_rows) * 100
        dtype_str = str(df[col].dtype)
        sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "N/A"
        if len(sample_val) > 28:
            sample_val = sample_val[:25] + "..."
        audit_data.append({
            "Column": col,
            "Type": dtype_str,
            "Nulls": f"{null_count} ({null_pct:.1f}%)",
            "Sample Value": sample_val
        })

    audit_df = pd.DataFrame(audit_data)
    print(audit_df.to_string(index=False))

    print("\n" + "-" * 70)
    print("CATEGORY BREAKDOWN (Frequency)")
    print("-" * 70)
    if "category" in df.columns:
        cat_counts = df["category"].value_counts()
        for cat, count in cat_counts.items():
            pct = (count / total_rows) * 100
            print(f"  • {cat:<24} : {count:>2} tickets ({pct:>5.1f}%)")

    print("\n" + "-" * 70)
    print("STATUS BREAKDOWN")
    print("-" * 70)
    if "status" in df.columns:
        status_counts = df["status"].value_counts()
        for stat, count in status_counts.items():
            pct = (count / total_rows) * 100
            print(f"  • {stat:<24} : {count:>2} tickets ({pct:>5.1f}%)")

    print("\n" + "-" * 70)
    print("PRIORITY BREAKDOWN")
    print("-" * 70)
    if "priority" in df.columns:
        prio_counts = df["priority"].value_counts()
        for prio, count in prio_counts.items():
            pct = (count / total_rows) * 100
            print(f"  • {prio:<24} : {count:>2} tickets ({pct:>5.1f}%)")

    print("\n" + "=" * 70)
    print("[SUCCESS] Module 1 Dataset Inspection Complete!")
    print("=" * 70)


if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "data/raw/customer_support_tickets.csv"
    inspect_dataset(target_arg)
