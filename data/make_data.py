from __future__ import annotations
import os
import random
from datetime import date, timedelta

import duckdb
import pandas as pd

DB_PATH = os.path.join("db", "analytics.duckdb")

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def main() -> None:
    os.makedirs("db", exist_ok=True)

    random.seed(42)

    start = date(2022, 1, 1)
    end = date(2025, 12, 31)

    regions = ["North", "South", "East", "West"]
    categories = ["Office Supplies", "Technology", "Furniture"]
    subcats = {
        "Office Supplies": ["Paper", "Binders", "Storage", "Pens"],
        "Technology": ["Phones", "Accessories", "Laptops", "Monitors"],
        "Furniture": ["Chairs", "Tables", "Bookcases"],
    }

    n = 25000
    rows = []
    for i in range(n):
        order_date = random_date(start, end)
        region = random.choice(regions)
        category = random.choice(categories)
        subcategory = random.choice(subcats[category])

        quantity = random.randint(1, 10)

        # category-shaped pricing
        if category == "Office Supplies":
            unit_price = round(random.uniform(5, 80), 2)
        elif category == "Furniture":
            unit_price = round(random.uniform(40, 900), 2)
        else:
            unit_price = round(random.uniform(50, 1200), 2)

        revenue = round(quantity * unit_price, 2)
        cost = round(revenue * random.uniform(0.55, 0.85), 2)
        profit = round(revenue - cost, 2)

        rows.append(
            {
                "order_id": f"O{i+1:06d}",
                "order_date": order_date.isoformat(),
                "region": region,
                "category": category,
                "subcategory": subcategory,
                "quantity": quantity,
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
            }
        )

    df = pd.DataFrame(rows)

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS orders AS SELECT * FROM df LIMIT 0;")
    con.execute("DELETE FROM orders;")
    con.execute("INSERT INTO orders SELECT * FROM df;")
    con.close()

    print(f"✅ Created DuckDB at: {DB_PATH}")
    print("✅ Table: orders")
    print(df.head(3).to_string(index=False))

if __name__ == "__main__":
    main()
