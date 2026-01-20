from __future__ import annotations
import re

ALLOWED_DIMENSIONS = {
    "region": "region",
    "category": "category",
    "subcategory": "subcategory",
}

ALLOWED_METRICS = {
    "revenue": "SUM(revenue) AS revenue",
    "sales": "SUM(revenue) AS revenue",
    "profit": "SUM(profit) AS profit",
    "cost": "SUM(cost) AS cost",
    "quantity": "SUM(quantity) AS quantity",
    "orders": "COUNT(*) AS orders",
}

def _year_filter(q: str) -> str | None:
    m = re.search(r"\b(20\d{2})\b", q)
    if not m:
        return None
    year = m.group(1)
    return f"EXTRACT(year FROM CAST(order_date AS DATE)) = {year}"

def _month_grouping(q: str) -> tuple[str | None, str | None]:
    if "by month" in q or "monthly" in q or "per month" in q:
        return ("month", "DATE_TRUNC('month', CAST(order_date AS DATE)) AS month")
    if "by day" in q or "daily" in q or "per day" in q:
        return ("day", "CAST(order_date AS DATE) AS day")
    if "by year" in q or "yearly" in q or "per year" in q:
        return ("year", "EXTRACT(year FROM CAST(order_date AS DATE)) AS year")
    return (None, None)

def _dimension_grouping(q: str) -> tuple[str | None, str | None]:
    for key, col in ALLOWED_DIMENSIONS.items():
        if f"by {key}" in q or f"per {key}" in q:
            return (col, f"{col} AS {col}")
    return (None, None)

def _metric(q: str) -> str:
    for k, expr in ALLOWED_METRICS.items():
        if k in q:
            return expr
    return "SUM(revenue) AS revenue"

def nl_to_sql(question: str) -> tuple[str | None, str]:
    q = question.strip().lower()

    if len(q) < 3:
        return None, "Question too short."

    where_clauses = []
    yf = _year_filter(q)
    if yf:
        where_clauses.append(yf)

    metric_expr = _metric(q)

    time_key, time_select = _month_grouping(q)
    dim_key, dim_select = _dimension_grouping(q)

    group_selects = []
    group_bys = []
    order_by = ""

    if time_select:
        group_selects.append(time_select)
        group_bys.append(time_key)
        order_by = f"ORDER BY {time_key} ASC"

    if dim_select:
        group_selects.append(dim_select)
        group_bys.append(dim_key)
        if not order_by:
            order_by = f"ORDER BY {dim_key} ASC"

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    if group_bys:
        select_list = ", ".join(group_selects + [metric_expr])
        group_by_list = ", ".join(group_bys)
        sql = f"""
        SELECT {select_list}
        FROM orders
        {where_sql}
        GROUP BY {group_by_list}
        {order_by}
        LIMIT 500
        """.strip()
        return sql, "OK (rules-based)"

    if "top" in q:
        sql = f"""
        SELECT category, {metric_expr}
        FROM orders
        {where_sql}
        GROUP BY category
        ORDER BY 2 DESC
        LIMIT 10
        """.strip()
        return sql, "OK (rules-based top-10)"

    sql = f"""
    SELECT {metric_expr}
    FROM orders
    {where_sql}
    """.strip()
    return sql, "OK (rules-based simple aggregate)"
