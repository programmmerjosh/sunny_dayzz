from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from cloud_cover_.data_loader import load_data
from cloud_cover_.helpers import flatten_cloud_cover
from ui import apply_theme, empty_state


st.set_page_config(page_title="Sunny Dayzz", page_icon="☀️", layout="wide")
apply_theme()

entries = load_data(Path(__file__).parent / "data" / "cloud_cover.json")
if not entries:
    empty_state("No weather data has been collected yet.")

same_day = [entry for entry in entries if entry.get("overview", {}).get("num_of_days_between_forecast") == 0]
frame = pd.DataFrame([row for entry in same_day for row in flatten_cloud_cover(entry)]).dropna(subset=["Cloud Cover (%)"])
if frame.empty:
    empty_state()

latest_date = frame["Date"].max()
latest = frame[frame["Date"] == latest_date]
location_summary = latest.groupby("Location", as_index=False)["Cloud Cover (%)"].mean().round(1)
provider_pivot = latest.pivot_table(index=["Location", "Time"], columns="Source", values="Cloud Cover (%)")
provider_gap = provider_pivot.max(axis=1) - provider_pivot.min(axis=1)

complete_sets = {}
for entry in entries:
    key = (entry.get("location"), entry.get("overview", {}).get("date_for"))
    complete_sets.setdefault(key, set()).add(entry.get("overview", {}).get("num_of_days_between_forecast"))
coverage = sum({0, 3, 5}.issubset(leads) for leads in complete_sets.values()) / max(len(complete_sets), 1) * 100

st.title("Will it feel sunny — and how early can we trust the call?")
st.caption("Same-day cloud outlooks and how 3- and 5-day forecasts changed as each date approached.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Locations", frame["Location"].nunique())
col2.metric("Days tracked", frame["Date"].nunique())
col3.metric("Latest outlook", latest_date.strftime("%d %b %Y"))
col4.metric("Complete lead coverage", f"{coverage:.0f}%")

st.subheader("Latest same-day outlook")
bar = (
    alt.Chart(location_summary)
    .mark_bar(cornerRadiusEnd=5)
    .encode(
        x=alt.X("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100]), title="Average cloud cover (%)"),
        y=alt.Y("Location:N", sort="x", title=None),
        color=alt.condition(alt.datum["Cloud Cover (%)"] <= 35, alt.value("#F4B942"), alt.value("#74859A")),
        tooltip=["Location", alt.Tooltip("Cloud Cover (%):Q", format=".1f")],
    )
    .properties(height=340)
)
st.altair_chart(bar, use_container_width=True)

left, right = st.columns(2)
left.metric("Average cloud", f"{latest['Cloud Cover (%)'].mean():.0f}%")
right.metric("Typical provider gap", f"{provider_gap.mean():.0f} pts")
st.caption("☀️ Gold bars are at or below the default 35% sunny threshold. “Same-day” is a forecast reference, not a measured observation.")
