from __future__ import annotations
import requests

def ollama_generate_sql(
    question: str,
    schema_text: str,
    model: str = "llama3.1:8b",
    timeout_s: int = 60,
) -> str:
    """
    Calls Ollama locally and returns SQL only (no markdown).
    """
    system = (
        "You are a senior data analyst. profiler: strict.\n"
        "Task: Convert the user's question into ONE valid DuckDB SQL SELECT query.\n"
        "Rules:\n"
        "- Use ONLY the tables/columns provided in the schema.\n"
        "- Output SQL only. No backticks. No markdown. No explanation.\n"
        "- Do NOT use semicolons.\n"
        "- Must be a single SELECT statement.\n"
        "- If user asks for a trend over time, group by month using "
        "DATE_TRUNC('month', CAST(order_date AS DATE)).\n"
        "- Keep results reasonably sized (use LIMIT 500 if returning many rows).\n"
    )

    prompt = f"""Schema:
{schema_text}

User question:
{question}

Return SQL only:"""

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

    # If the model disobeys and adds code fences, strip them.
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql
