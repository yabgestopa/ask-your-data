from __future__ import annotations
import re

FORBIDDEN = [
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "attach", "detach", "copy", "export", "import"
]

def is_safe_sql(sql: str) -> tuple[bool, str]:
    s = sql.strip().lower()

    if not s.startswith("select"):
        return False, "Only SELECT queries are allowed."

    # avoid multi-statement queries
    if ";" in s:
        return False, "Semicolons are not allowed."

    for kw in FORBIDDEN:
        if re.search(rf"\b{re.escape(kw)}\b", s):
            return False, f"Forbidden keyword detected: {kw}"

    return True, "OK"
