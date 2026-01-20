from __future__ import annotations
import requests

def ollama_repair_sql(
    bad_sql: str,
    error_message: str,
    schema_text: str,
    model: str = "llama3.1:8b",
    timeout_s: int = 60,
) -> str:
    system = (
        "You are a senior analytics engineer.\n"
        "Fix the SQL so it runs in DuckDB.\n"
        "Rules:\n"
        "- Output SQL only (no markdown, no explanation, no semicolons).\n"
        "- Must be a single SELECT statement.\n"
        "- Use ONLY the provided schema.\n"
        "- If a column/table is wrong, replace it with the closest valid one.\n"
        "- Keep results reasonably sized (LIMIT 500 if many rows).\n"
        "- If you use strftime, DATE_TRUNC, EXTRACT, or date functions, always CAST date-like columns to DATE first (e.g., CAST(order_date AS DATE)).\n"
    )

    prompt = f"""Schema:
{schema_text}

Bad SQL:
{bad_sql}

DuckDB error:
{error_message}

Return a corrected SQL query only:"""

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }

    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    sql = (data.get("response") or "").strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql
