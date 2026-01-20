from __future__ import annotations

import os
import streamlit as st

from src.db import run_query, get_schema_text
from src.safe_sql import is_safe_sql
from src.nl2sql_rules import nl_to_sql
from src.charts import pick_chart
from src.llm_ollama import ollama_generate_sql
from src.llm_sql_repair import ollama_repair_sql

DB_PATH = os.path.join("db", "analytics.duckdb")

st.set_page_config(page_title="Ask Your Data (DuckDB)", layout="wide")

st.title("Ask Your Data 🦆📊")
st.caption(
    "Type a business question. The app generates SQL, runs it on DuckDB, "
    "and shows results + a chart."
)

# Basic safety check: ensure DB exists
if not os.path.exists(DB_PATH):
    st.error(f"Database not found at {DB_PATH}. Run: python data\\make_data.py")
    st.stop()

with st.expander("Dataset schema"):
    st.code(get_schema_text(DB_PATH), language="text")

examples = [
    "Total revenue in 2024",
    "Monthly revenue in 2024",
    "Profit by region in 2023",
    "Monthly profit by category in 2025",
    "Monthly revenue by category in 2024",
    "Top categories by revenue in 2024",
]

left, right = st.columns([2, 1], gap="large")

with right:
    st.subheader("Try examples")
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["question"] = ex

with left:
    mode = st.radio(
        "Query mode",
        ["Rules (fast)", "AI (Ollama)"],
        horizontal=True,
    )

    question = st.text_input(
        "Your question",
        key="question",
        placeholder="e.g., Monthly revenue by category in 2024",
    )

    run_btn = st.button("Ask", type="primary")

    if run_btn:
        # 1) Generate SQL
        if mode == "Rules (fast)":
            sql, note = nl_to_sql(question)
        else:
            schema_text = get_schema_text(DB_PATH)
            sql = ollama_generate_sql(question=question, schema_text=schema_text)
            note = "OK (AI via Ollama)"

        if not sql or len(sql.strip()) < 10:
            st.error("No SQL returned by the model. Try rephrasing your question.")
            st.stop()

        # 2) Guardrails
        ok, reason = is_safe_sql(sql)
        if not ok:
            st.error(f"Blocked SQL: {reason}")
            st.code(sql, language="sql")
            st.stop()

        st.subheader("Generated SQL")
        st.code(sql, language="sql")
        st.caption(note)

        # 3) Run SQL (repair once if AI mode fails)
        try:
            df = run_query(DB_PATH, sql)
        except Exception as e:
            if mode == "AI (Ollama)":
                st.warning("AI SQL failed. Attempting an automatic repair...")

                schema_text = get_schema_text(DB_PATH)
                repaired_sql = ollama_repair_sql(
                    bad_sql=sql,
                    error_message=str(e),
                    schema_text=schema_text,
                )

                ok2, reason2 = is_safe_sql(repaired_sql)
                if not ok2:
                    st.error(f"Repaired SQL was blocked: {reason2}")
                    st.code(repaired_sql, language="sql")
                    st.stop()

                st.subheader("Repaired SQL")
                st.code(repaired_sql, language="sql")

                try:
                    df = run_query(DB_PATH, repaired_sql)
                    sql = repaired_sql
                except Exception as e2:
                    st.error("Repair attempt failed.")
                    st.exception(e2)
                    st.stop()
            else:
                st.error("Query failed.")
                st.exception(e)
                st.stop()

        # 4) Results
        st.subheader("Result")
        st.dataframe(df, use_container_width=True, height=360)

        # 5) Chart
        chart_df, chart_note = pick_chart(df)
        st.subheader("Chart")
        st.caption(chart_note)

        if chart_df is None:
            st.info("No chart for this result.")
        else:
            import pandas as pd
            import altair as alt

            plot_df = chart_df.copy()

            # If datetime index, keep it and ensure sorted
            if isinstance(plot_df.index, pd.DatetimeIndex):
                plot_df = plot_df.sort_index()
                # Build a display label like "Jan 2024" for axis
                plot_df = plot_df.reset_index().rename(columns={"index": "month"})
                plot_df["month_label"] = plot_df["month"].dt.strftime("%b %Y")
            else:
                plot_df = plot_df.reset_index()
                plot_df.rename(columns={plot_df.columns[0]: "x"}, inplace=True)
                plot_df["month_label"] = plot_df["x"].astype(str)

            # Convert wide (clustered columns) to long for Altair
            if "month" in plot_df.columns:
                id_col = "month"
            else:
                id_col = plot_df.columns[0]

            value_cols = [c for c in plot_df.columns if c not in (id_col, "month_label", "x")]

            long_df = plot_df.melt(
                id_vars=[id_col, "month_label"],
                value_vars=value_cols,
                var_name="series",
                value_name="value"
            )

            # Ensure correct month ordering using the real datetime column
            sort_field = id_col

            # Build chart
            chart = (
                alt.Chart(long_df)
                .mark_bar()
                .encode(
                    x=alt.X("month_label:N", sort=alt.SortField(sort_field, order="ascending"), title=""),
                    y=alt.Y("value:Q", title=""),
                    xOffset="series:N",  # clustered bars
                    color="series:N",
                    tooltip=[
                        alt.Tooltip("series:N", title="Series"),
                        alt.Tooltip("month_label:N", title="Month"),
                        alt.Tooltip("value:Q", title="Value", format=",.0f"),
                    ],
                )
                .properties(height=380)
                .interactive()  # keeps pan/zoom (hover already works)
            )

            st.altair_chart(chart, use_container_width=True)
