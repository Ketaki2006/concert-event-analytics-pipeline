"""Streamlit dashboard for the synthetic concert and event dataset."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "events.db"
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "data_quality_report.json"
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(page_title="Concert & Event Analytics", page_icon="♫", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #f4f6f3; color: #182824; }
    [data-testid="stHeader"] { background: rgba(244, 246, 243, .92); }
    .eyebrow { color: #a3432b; font-size: .76rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
    .main-title { color: #183b34; font-family: Georgia, serif; font-size: 2.35rem; margin: 0 0 .15rem; }
    .synthetic-note { background: #e6eee8; border-left: 4px solid #3c7964; padding: .75rem 1rem; margin: 1rem 0; }
    [data-testid="stMetric"] { background: #fff; border: 1px solid #dce4dd; border-radius: 6px; padding: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    with sqlite3.connect(DATABASE_PATH) as connection:
        return pd.read_sql_query("SELECT * FROM events ORDER BY event_date", connection)


def load_quality_report() -> dict[str, object]:
    if not REPORT_PATH.exists():
        return {}
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


st.markdown('<div class="eyebrow">Data engineering project / local demo</div>', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">Concert &amp; Event Analytics</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="synthetic-note"><strong>Synthetic data only.</strong> '
    'All events, attendance, ticket values, and revenue are fictional and generated for education. '
    'They are not real-world sales or attendance figures.</div>',
    unsafe_allow_html=True,
)

if not DATABASE_PATH.exists():
    st.warning("No processed database found. Run `python -m src.generate_data` and `python -m src.etl` first.")
    st.stop()

events = load_data()
if events.empty:
    st.info("The database contains no events. Rerun the data generator and ETL pipeline.")
    st.stop()

with st.sidebar:
    st.subheader("Explore events")
    city_options = sorted(events["city"].dropna().unique().tolist())
    genre_options = sorted(events["genre"].dropna().unique().tolist())
    selected_cities = st.multiselect("City", city_options, default=city_options)
    selected_genres = st.multiselect("Genre", genre_options, default=genre_options)

filtered = events[events["city"].isin(selected_cities) & events["genre"].isin(selected_genres)].copy()
filtered["event_date"] = pd.to_datetime(filtered["event_date"])

total_revenue = filtered["revenue"].sum()
average_occupancy = filtered["occupancy_rate"].mean() * 100 if not filtered.empty else 0
kpi_columns = st.columns(4)
kpi_columns[0].metric("Events", f"{len(filtered):,}")
kpi_columns[1].metric("Synthetic tickets", f"{filtered['tickets_sold'].sum():,}")
kpi_columns[2].metric("Derived synthetic revenue", f"${total_revenue:,.0f}")
kpi_columns[3].metric("Average occupancy", f"{average_occupancy:.1f}%")

st.subheader("Monthly activity")
monthly = (
    filtered.groupby("month_label", as_index=False)
    .agg(event_count=("event_id", "count"), tickets_sold=("tickets_sold", "sum"))
    .sort_values("month_label")
)
chart_left, chart_right = st.columns(2)
with chart_left:
    st.plotly_chart(
        px.bar(monthly, x="month_label", y="event_count", title="Events per month", labels={"month_label": "Month", "event_count": "Events"}, color_discrete_sequence=["#3c7964"]),
        use_container_width=True,
    )
with chart_right:
    st.plotly_chart(
        px.line(monthly, x="month_label", y="tickets_sold", title="Synthetic tickets per month", labels={"month_label": "Month", "tickets_sold": "Tickets"}, markers=True, color_discrete_sequence=["#c46b45"]),
        use_container_width=True,
    )

st.subheader("Events")
display_columns = ["event_date", "event_name", "city", "venue", "genre", "capacity", "tickets_sold", "ticket_price", "revenue"]
st.dataframe(filtered[display_columns].sort_values("event_date", ascending=False), use_container_width=True, hide_index=True)
st.download_button(
    "Download filtered events as CSV",
    data=filtered[display_columns].to_csv(index=False).encode("utf-8"),
    file_name="synthetic_events.csv",
    mime="text/csv",
)

with st.expander("Data quality report", expanded=False):
    quality = load_quality_report()
    if not quality:
        st.info("No report found. Run the ETL pipeline to generate it.")
    else:
        quality_columns = st.columns(4)
        quality_columns[0].metric("Source rows", f"{quality.get('source_rows', 0):,}")
        quality_columns[1].metric("Exact duplicates", f"{quality.get('duplicate_rows', 0):,}")
        quality_columns[2].metric("Duplicate event IDs", f"{quality.get('duplicate_event_ids', 0):,}")
        quality_columns[3].metric("Invalid rows removed", f"{quality.get('invalid_rows', 0):,}")
        st.write("Missing values before cleaning")
        missing = quality.get("missing_values_by_column", {})
        if missing:
            st.dataframe(pd.DataFrame([{"column": key, "missing_values": value} for key, value in missing.items()]), hide_index=True, use_container_width=True)
        else:
            st.write("No missing values found.")
        st.caption(f"Clean rows loaded: {quality.get('clean_rows', 0):,}. Synthetic data only.")