"""KPI Glossary Page (Multipage Friendly)."""

import ast
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1qRZ6vBfhh1-hqnERBeI6QuJVqyb2b8z8SjYTQkC1X1I/edit?usp=sharing"


@st.cache_data(ttl=300)
def load_kpi_data(sheet_url: str) -> pd.DataFrame:
    """Load KPI data from a Google Sheet.

    This function retrieves KPI data from a specified Google Sheet URL and returns it as a Pandas DataFrame.

    Args:
        sheet_url (str): The URL of the Google Sheet to load data from.

    Returns:
        pd.DataFrame: A DataFrame containing the KPI data.
    """
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=sheet_url, usecols=list(range(5)))
    df.columns = [c.lower().strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date", "name"])


def parse_todo(raw: Any) -> list[str]:
    """Parse todo items from raw data.

    Converts various input formats (string, list, etc.) into a list of strings.
    Handles AST literal evaluation for string representations of lists.

    Args:
        raw: Raw todo data that can be string, list, or other format

    Returns:
        list[str]: List of todo items as strings
    """
    if not raw or pd.isna(raw):
        return []
    try:
        if isinstance(raw, str):
            parsed = ast.literal_eval(raw)
            return (
                [str(p) for p in parsed] if isinstance(parsed, list) else [str(parsed)]
            )
        return [str(raw)]
    except Exception:
        return [str(raw)]


def filter_kpi_data(df: pd.DataFrame, selected_date: date, query: str) -> pd.DataFrame:
    """Filter KPI data by date and search query."""
    filtered = df[df["date"].dt.date == selected_date]

    if query:
        q = query.lower()
        filtered = filtered[
            filtered["name"].str.lower().str.contains(q, na=False)
            | filtered["description"].str.lower().str.contains(q, na=False)
        ]

    return filtered


def display_kpi_item(row: pd.Series) -> None:
    """Display individual KPI item in expander."""
    with st.expander(f"📊 {row['name']}"):
        if row.get("description"):
            st.markdown(f"**📝 Deskripsi:**\n{row['description']}")

        todos = parse_todo(row.get("todo"))
        if todos:
            st.markdown("**✅ TODO:**")
            for i, item in enumerate(todos, 1):
                st.markdown(f"{i}. {item}")

        if row.get("insentif") and str(row["insentif"]).strip().lower() != "ngga ada":
            st.success(f"💰 {row['insentif']}")


def render_kpi_page():
    """Render the KPI Glossary page.

    This page allows users to view and filter KPIs from a Google Sheet.
    """
    st.header("📘 KPI Glossary")

    sheet_url = st.text_input(
        "📎 Google Sheets URL",
        value=DEFAULT_SHEET_URL,
        help="Ganti URL jika sumber data berubah",
    )

    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

    try:
        df = load_kpi_data(sheet_url)

        col1, col2 = st.columns([1, 2])

        with col1:
            selected_date = st.selectbox(
                "📅 Tanggal",
                options=sorted(df["date"].dt.date.unique(), reverse=True),
                format_func=lambda x: x.strftime("%d %b %Y"),
            )

        with col2:
            query = st.text_input("🔍 Cari KPI")

        filtered = filter_kpi_data(df, selected_date, query)

        st.markdown(
            f"**📌 {len(filtered)} KPI untuk {selected_date.strftime('%d %B %Y')}**"
        )
        if query:
            st.caption(f"Filter: `{query}`")

        if filtered.empty:
            st.warning("⚠️ Tidak ada KPI")
            return

        for _, row in filtered.iterrows():
            display_kpi_item(row)

    except Exception as e:
        st.error(f"❌ Gagal load data: {e}")
        st.info("Pastikan URL Sheet bisa diakses publik")


# Untuk multipage mode
if __name__ == "__main__" or __name__ == "__streamlit__":
    render_kpi_page()
