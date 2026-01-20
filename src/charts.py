from __future__ import annotations
import pandas as pd


def pick_chart(df: pd.DataFrame):
    """
    Returns a (chart_df, note) tuple.

    - If the result contains month + category + numeric metric, returns a pivoted
      dataframe suitable for a clustered column chart:
        index: month (datetime)
        columns: categories
        values: metric

    - Otherwise returns a simple dataframe indexed by the first column with the first
      numeric column as values.
    """
    if df is None or df.empty:
        return None, "No data to chart."

    cols = df.columns.tolist()

    # Case 1: clustered chart (month + category + metric)
    if set(["month", "category"]).issubset(cols):
        metric_cols = [
            c for c in cols
            if c not in ("month", "category")
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        if not metric_cols:
            return None, "No numeric metric to chart."

        metric = metric_cols[0]

        pivot = (
            df.assign(month=pd.to_datetime(df["month"]))
              .pivot_table(
                  index="month",
                  columns="category",
                  values=metric,
                  aggfunc="sum"
              )
              .sort_index()
        )

        return pivot, f"Clustered column chart: {metric} by category per month"

    # Case 2: simple chart (dimension + metric)
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    if len(cols) >= 2 and numeric_cols:
        x = cols[0]
        y = numeric_cols[0]

        chart_df = df[[x, y]].copy()

        # If x looks like datetime, parse it and sort
        try:
            chart_df[x] = pd.to_datetime(chart_df[x])
        except Exception:
            pass

        chart_df = chart_df.set_index(x).sort_index()
        return chart_df, f"Column chart: {y} by {x}"

    return None, "No suitable chart found."
