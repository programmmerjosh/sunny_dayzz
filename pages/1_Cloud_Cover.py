from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from cloud_cover_.data_loader import get_filtered_data, load_data
from cloud_cover_.helpers import flatten_cloud_cover
from ui import apply_theme, empty_state


st.set_page_config(page_title="Same-day outlook", page_icon="☀️", layout="wide")
apply_theme()

data_path = Path(__file__).parents[1] / "data" / "cloud_cover.json"
data = load_data(data_path)
if not data:
    empty_state("No weather data has been collected yet.")

locations = sorted({entry.get("location") for entry in data if entry.get("location")})
with st.sidebar:
    selected_location = st.selectbox("Location", locations)
    window = st.selectbox("History", [30, 90, "All"], format_func=lambda value: f"Last {value} days" if isinstance(value, int) else value)
    sunny_threshold = st.slider("Sunny below (% cloud)", 10, 70, 35)

entries = [
    entry
    for entry in get_filtered_data(data, selected_location)
    if entry.get("overview", {}).get("num_of_days_between_forecast") == 0
]
frame = pd.DataFrame([row for entry in entries for row in flatten_cloud_cover(entry)]).dropna(subset=["Cloud Cover (%)"])
if frame.empty:
    empty_state()

sources = sorted(frame["Source"].unique())
with st.sidebar:
    selected_sources = st.multiselect("Providers", sources, default=sources)
if not selected_sources:
    empty_state("Select at least one provider.")

frame = frame[frame["Source"].isin(selected_sources)].copy()
if isinstance(window, int):
    cutoff = frame["Date"].max() - pd.Timedelta(days=window - 1)
    frame = frame[frame["Date"] >= cutoff]

frame["Hour"] = frame["Time"].str.slice(0, 2).astype(int)
frame["Period"] = pd.cut(frame["Hour"], bins=[0, 10, 16, 24], labels=["Morning", "Afternoon", "Evening"])
daily = frame.groupby(["Date", "Source"], as_index=False)["Cloud Cover (%)"].mean()
day_average = frame.groupby("Date", as_index=False)["Cloud Cover (%)"].mean()
day_average["Sunny"] = day_average["Cloud Cover (%)"] <= sunny_threshold
provider_pivot = frame.pivot_table(index=["Date", "Time"], columns="Source", values="Cloud Cover (%)")
gaps = provider_pivot.max(axis=1) - provider_pivot.min(axis=1)
periods = frame.groupby(["Date", "Period"], observed=True, as_index=False)["Cloud Cover (%)"].mean()
periods["Sunny"] = periods["Cloud Cover (%)"] <= sunny_threshold
sunny_by_period = periods.groupby("Period", observed=True, as_index=False)["Sunny"].mean()
sunny_by_period["Sunny share (%)"] = sunny_by_period["Sunny"] * 100
clearest = sunny_by_period.sort_values("Sunny share (%)", ascending=False).iloc[0]

st.title(f"☀️ Same-day outlook · {selected_location}")
st.caption("What the providers expected between 06:00 and 18:00 UTC on each day.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sunny days", f"{day_average['Sunny'].mean() * 100:.0f}%")
col2.metric("Average cloud", f"{frame['Cloud Cover (%)'].mean():.0f}%")
col3.metric("Clearest period", str(clearest["Period"]))
col4.metric("Provider gap", f"{gaps.mean():.0f} pts")

st.subheader("Cloud cover at a glance")
heatmap_data = frame.groupby(["Date", "Time"], as_index=False)["Cloud Cover (%)"].mean()
heatmap = (
    alt.Chart(heatmap_data)
    .mark_rect(cornerRadius=2)
    .encode(
        x=alt.X("yearmonthdate(Date):O", title=None, axis=alt.Axis(labelAngle=-45, format="%d %b")),
        y=alt.Y("Time:O", sort=["06:00 UTC", "09:00 UTC", "12:00 UTC", "15:00 UTC", "18:00 UTC"], title=None),
        color=alt.Color("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100], range=["#F7CF62", "#B8C7D9", "#40536B"]), title="Cloud %"),
        tooltip=[alt.Tooltip("Date:T", format="%d %b %Y"), "Time", alt.Tooltip("Cloud Cover (%):Q", format=".0f")],
    )
    .properties(height=230)
)
st.altair_chart(heatmap, use_container_width=True)

left, right = st.columns([2, 1])
with left:
    st.subheader("Daily outlook by provider")
    trend = (
        alt.Chart(daily)
        .mark_line(point=False, strokeWidth=2)
        .encode(
            x=alt.X(
                "Date:T",
                title=None,
                axis=alt.Axis(
                    format="%d %b",
                    labelAngle=0,
                    labelFlush=False,
                    labelOverlap="greedy",
                    labelPadding=10,
                    tickCount="week",
                ),
            ),
            y=alt.Y("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100]), title="Daily cloud (%)"),
            color=alt.Color("Source:N", title=None),
            tooltip=[alt.Tooltip("Date:T", format="%d %b %Y"), "Source", alt.Tooltip("Cloud Cover (%):Q", format=".0f")],
        )
        .properties(height=300, padding={"bottom": 32})
    )
    st.altair_chart(trend, use_container_width=True)
with right:
    st.subheader("Sunny by period")
    period_chart = (
        alt.Chart(sunny_by_period)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#F4B942")
        .encode(
            x=alt.X("Period:N", title=None, sort=["Morning", "Afternoon", "Evening"]),
            y=alt.Y("Sunny share (%):Q", scale=alt.Scale(domain=[0, 100]), title="Days below threshold (%)"),
            tooltip=["Period", alt.Tooltip("Sunny share (%):Q", format=".0f")],
        )
        .properties(height=300)
    )
    st.altair_chart(period_chart, use_container_width=True)

latest_date = frame["Date"].max()
latest = frame[frame["Date"] == latest_date]
st.subheader(f"Latest day · {latest_date.strftime('%d %b %Y')}")
latest_chart = (
    alt.Chart(latest)
    .mark_line(point=alt.OverlayMarkDef(size=70), strokeWidth=3)
    .encode(
        x=alt.X("Time:O", title="UTC"),
        y=alt.Y("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100]), title="Cloud cover (%)"),
        color=alt.Color("Source:N", title=None),
        tooltip=["Time", "Source", "Cloud Cover (%)"],
    )
    .properties(height=280)
)
threshold_line = alt.Chart(pd.DataFrame({"threshold": [sunny_threshold]})).mark_rule(color="#F4B942", strokeDash=[6, 4]).encode(y="threshold:Q")
st.altair_chart(latest_chart + threshold_line, use_container_width=True)
