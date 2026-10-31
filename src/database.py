"""
SQL Database and Storage Module
Module 4: Customer Support Ticket Analytics & GenAI Business Assistant

Persists cleaned support ticket records in SQLite:
- Creates and manages the SQLite database schema
- Enforces primary key uniqueness on ticket_id
- Implements idempotent data insertion (duplicate prevention on repeated imports)
- Uses atomic transactions to prevent partial writes
- Provides parameterised SQL execution and data retrieval helpers
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Union, Tuple, List, Dict, Any
import pandas as pd
from dotenv import load_dotenv

# Add project root to sys.path so modules can run standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment configuration
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_DB_PATH = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/processed/customer_support.db")


def get_db_path(db_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolves and returns the target SQLite database Path."""
    if db_path is None:
        target = DEFAULT_DB_PATH
    else:
        target = Path(db_path)
    # Ensure parent directory exists
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Creates and returns an active connection to the SQLite database.
    Enables foreign keys and sets row_factory to sqlite3.Row.
    """
    resolved_path = get_db_path(db_path)
    conn = sqlite3.connect(resolved_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """
    Initialises the database schema:
    - tickets: Core table storing cleaned ticket records
    - ingestion_logs: Audit table tracking batch imports
    - Indexes for query optimization
    """
    resolved_path = get_db_path(db_path)
    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # 1. Support Tickets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                resolution_notes TEXT,
                resolution_time_hours REAL,
                is_unresolved INTEGER NOT NULL CHECK (is_unresolved IN (0, 1)),
                inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Performance Indexes on Frequent Filter & Aggregation Columns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_unresolved ON tickets(is_unresolved);")

        # 3. Batch Ingestion Audit Log Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                total_received INTEGER NOT NULL,
                records_inserted INTEGER NOT NULL,
                records_skipped INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()


def insert_tickets(
    df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
    source_name: str = "csv_upload",
    conflict_strategy: str = "IGNORE"
) -> Tuple[int, int]:
    """
    Inserts cleaned ticket records into the database with duplicate prevention.

    Parameters:
        df: DataFrame containing transformed ticket records.
        db_path: Optional SQLite database file path.
        source_name: Name or path of the ingested file (for ingestion log).
        conflict_strategy: 'IGNORE' (default, skips duplicate ticket_id) or
                           'REPLACE' (overwrites existing ticket_id).

    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    if df.empty:
        return 0, 0

    init_db(db_path)
    resolved_path = get_db_path(db_path)

    insert_sql = f"""
        INSERT OR {conflict_strategy.upper()} INTO tickets (
            ticket_id, customer_id, created_at, resolved_at,
            category, priority, status, subject, description,
            resolution_notes, resolution_time_hours, is_unresolved
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    # Prepare records as tuples for parameterised insertion
    records = []
    for _, row in df.iterrows():
        records.append((
            str(row["ticket_id"]),
            str(row.get("customer_id", "CUST-UNKNOWN")),
            str(row["created_at"]),
            str(row["resolved_at"]) if pd.notna(row.get("resolved_at")) else None,
            str(row["category"]),
            str(row["priority"]),
            str(row["status"]),
            str(row["subject"]),
            str(row["description"]),
            str(row["resolution_notes"]) if pd.notna(row.get("resolution_notes")) else None,
            float(row["resolution_time_hours"]) if pd.notna(row.get("resolution_time_hours")) else None,
            int(row["is_unresolved"])
        ))

    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # Count existing tickets before insertion
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        count_before = cursor.fetchone()[0]

        # Parameterised batch insert within transaction
        cursor.executemany(insert_sql, records)

        # Count tickets after insertion
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        count_after = cursor.fetchone()[0]

        inserted_count = count_after - count_before
        skipped_count = len(records) - inserted_count

        # Record ingestion audit log
        cursor.execute("""
            INSERT INTO ingestion_logs (source_name, total_received, records_inserted, records_skipped)
            VALUES (?, ?, ?, ?);
        """, (source_name, len(records), inserted_count, skipped_count))

        conn.commit()

    return inserted_count, skipped_count


def get_ticket_count(db_path: Optional[Union[str, Path]] = None) -> int:
    """Returns the total number of ticket records stored in the database."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        return cursor.fetchone()[0]


def get_all_tickets(
    db_path: Optional[Union[str, Path]] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """Retrieves stored tickets ordered by created_at descending."""
    init_db(db_path)
    sql = "SELECT * FROM tickets ORDER BY created_at DESC"
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return execute_query(sql, db_path=db_path)


def execute_query(
    sql: str,
    params: Optional[tuple] = None,
    db_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Executes a parameterised SQL SELECT query and returns the results as a pandas DataFrame.
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        if params is None:
            return pd.read_sql_query(sql, conn)
        return pd.read_sql_query(sql, conn, params=params)


if __name__ == "__main__":
    from src.ingestion import read_csv_tickets
    from src.transformation import clean_and_transform_tickets

    print("=" * 65)
    print("SQL DATABASE & STORAGE DEMONSTRATION")
    print("=" * 65)

    sample_csv = "data/raw/customer_support_tickets.csv"
    print(f"\n1. Ingesting raw CSV: {sample_csv}")
    ing_res = read_csv_tickets(sample_csv)
    print(f"   [OK] Ingested {ing_res.record_count} records.")

    print("\n2. Transforming records...")
    clean_df, dq_report = clean_and_transform_tickets(ing_res.data)
    print(f"   [OK] Cleaned {len(clean_df)} records (Accepted: {dq_report.accepted}).")

    print("\n3. Initializing SQLite Database...")
    init_db()
    db_loc = get_db_path()
    print(f"   [OK] Database active at: {db_loc}")

    print("\n4. First Import Batch (Inserting cleaned tickets)...")
    inserted, skipped = insert_tickets(clean_df, source_name="initial_import")
    print(f"   [OK] Inserted: {inserted} | Skipped/Duplicate: {skipped}")
    print(f"   [OK] Current Database Total: {get_ticket_count()} tickets.")

    print("\n5. Testing Duplicate Prevention (Re-importing the same dataset)...")
    inserted_2, skipped_2 = insert_tickets(clean_df, source_name="repeated_import")
    print(f"   [OK] Inserted: {inserted_2} | Skipped/Duplicate: {skipped_2}")
    print(f"   [OK] Database Total After Re-import: {get_ticket_count()} tickets.")

    if inserted_2 == 0 and skipped_2 == len(clean_df):
        print("\n[SUCCESS] Duplicate prevention verified: 0 duplicate records created!")
    else:
        print("\n[WARNING] Duplicate check failed.")

    print("\n6. Sample SQL Query Verification:")
    sample_df = execute_query("SELECT ticket_id, status, category, priority, resolution_time_hours FROM tickets LIMIT 3;")
    print(sample_df.to_string(index=False))
    print("=" * 65)
