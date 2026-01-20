from __future__ import annotations
import duckdb
import pandas as pd

def run_query(db_path: str, sql: str) -> pd.DataFrame:
    con = duckdb.connect(db_path, read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()

def get_schema_text(db_path: str) -> str:
    con = duckdb.connect(db_path, read_only=True)
    try:
        cols = con.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
            """
        ).fetchall()
    finally:
        con.close()

    lines = ["Table: orders", "Columns:"]
    for name, dtype in cols:
        lines.append(f"- {name} ({dtype})")
    return "\n".join(lines)
