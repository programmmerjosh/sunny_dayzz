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
    sunny_threshold = st.slider("Sunny-day limit", 10, 70, 35, format="%d%% cloud")
    st.caption(f"A day counts as mostly clear at {sunny_threshold}% cloud or less.")

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
provider_counts = provider_pivot.notna().sum(axis=1)
gaps = (provider_pivot.max(axis=1) - provider_pivot.min(axis=1))[provider_counts >= 2]
periods = frame.groupby(["Date", "Period"], observed=True, as_index=False)["Cloud Cover (%)"].mean()
periods["Clear Sky (%)"] = 100 - periods["Cloud Cover (%)"]
periods["Sunny"] = periods["Cloud Cover (%)"] <= sunny_threshold
sunny_by_period = (
    periods.groupby("Period", observed=True, as_index=False)
    .agg(
        **{
            "Mostly clear days": ("Sunny", "sum"),
            "Total days": ("Date", "nunique"),
        }
    )
)
sunny_by_period["Sunny share (%)"] = (
    sunny_by_period["Mostly clear days"] / sunny_by_period["Total days"] * 100
)
sunny_by_period["Bar label"] = sunny_by_period.apply(
    lambda row: f"{int(row['Mostly clear days'])}/{int(row['Total days'])} · {row['Sunny share (%)']:.0f}%",
    axis=1,
)
clearest = sunny_by_period.sort_values("Sunny share (%)", ascending=False).iloc[0]

st.title(f"When was {selected_location} expected to have clear skies?")
st.caption("Same-day forecasts between 06:00 and 18:00 UTC. These are provider outlooks, not measured weather observations.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Mostly clear days", f"{day_average['Sunny'].mean() * 100:.0f}%")
col2.metric("Typical clear sky", f"{100 - day_average['Cloud Cover (%)'].mean():.0f}%")
col3.metric("Clearest time", str(clearest["Period"]))
col4.metric("Typical provider difference", f"{gaps.mean():.0f} pts" if not gaps.empty else "Not available")

st.subheader("Clear sky by time of day")
provider_names = [source.replace(".com", "") for source in selected_sources]
if len(provider_names) == 1:
    provider_description = provider_names[0]
else:
    provider_description = " and ".join(provider_names)
st.caption(
    f"Each square shows one date and one part of the day, averaged across {provider_description}. "
    "More gold means clearer skies; more grey means more cloud."
)
heatmap_data = periods.copy()
heatmap_data["Cloud cover display (%)"] = heatmap_data["Cloud Cover (%)"].round().astype(int)
heatmap_data["Clear sky display (%)"] = 100 - heatmap_data["Cloud cover display (%)"]
heatmap = (
    alt.Chart(heatmap_data)
    .mark_rect(cornerRadius=3, strokeWidth=2)
    .encode(
        x=alt.X("yearmonthdate(Date):O", title=None, axis=alt.Axis(labelAngle=-45, format="%d %b")),
        y=alt.Y("Period:N", sort=["Morning", "Afternoon", "Evening"], title=None),
        color=alt.Color(
            "Clear Sky (%):Q",
            scale=alt.Scale(
                domain=[0, 50, 100],
                range=["#657184", "#D9DDE2", "#F4B942"],
                interpolate="rgb",
            ),
            title="Clear sky %",
        ),
        stroke=alt.condition(
            alt.datum["Cloud Cover (%)"] <= sunny_threshold,
            alt.value("#C98708"),
            alt.value("transparent"),
        ),
        tooltip=[
            alt.Tooltip("Date:T", format="%d %b %Y"),
            "Period:N",
            alt.Tooltip("Clear sky display (%):Q", format="d", title="Clear Sky (%)"),
            alt.Tooltip("Cloud cover display (%):Q", format="d", title="Cloud Cover (%)"),
        ],
    )
    .properties(height=180)
)
st.altair_chart(heatmap, use_container_width=True)
st.caption(
    f"A gold outline marks periods at or below the selected {sunny_threshold}% cloud limit. "
    "Morning combines 06:00 and 09:00, Afternoon combines 12:00 and 15:00, and Evening is 18:00 UTC."
)

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
        color=alt.Color("Source:N", title=None, legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("Date:T", format="%d %b %Y"), "Source", alt.Tooltip("Cloud Cover (%):Q", format=".0f")],
    )
    .properties(height=300, padding={"bottom": 32})
)

latest_date = frame["Date"].max()
latest = frame[frame["Date"] == latest_date]
latest_chart = (
    alt.Chart(latest)
    .mark_line(point=alt.OverlayMarkDef(size=70), strokeWidth=3)
    .encode(
        x=alt.X("Time:O", title="UTC", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100]), title="Cloud cover (%)"),
        color=alt.Color("Source:N", title=None, legend=alt.Legend(orient="top")),
        tooltip=["Time", "Source", "Cloud Cover (%)"],
    )
    .properties(height=300)
)
threshold_line = (
    alt.Chart(pd.DataFrame({"threshold": [sunny_threshold]}))
    .mark_rule(color="#F4B942", strokeDash=[6, 4])
    .encode(y="threshold:Q")
)

st.subheader("Provider outlooks")
left, right = st.columns(2)
with left:
    st.subheader("Daily outlook by provider")
    st.altair_chart(trend, use_container_width=True)
with right:
    st.subheader(f"Latest day · {latest_date.strftime('%d %b %Y')}")
    st.altair_chart(latest_chart + threshold_line, use_container_width=True)

with st.container(border=True):
    st.subheader("How often was each part of the day mostly clear?")
    period_bars = (
        alt.Chart(sunny_by_period)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#F4B942")
        .encode(
            x=alt.X(
                "Period:N",
                title=None,
                sort=["Morning", "Afternoon", "Evening"],
                scale=alt.Scale(paddingInner=0.65, paddingOuter=0.35),
            ),
            y=alt.Y(
                "Sunny share (%):Q",
                scale=alt.Scale(domain=[0, 100]),
                title="Share of selected days (%)",
            ),
            tooltip=[
                "Period:N",
                alt.Tooltip("Mostly clear days:Q", format="d"),
                alt.Tooltip("Total days:Q", format="d"),
                alt.Tooltip("Sunny share (%):Q", format=".0f"),
            ],
        )
    )
    period_labels = (
        alt.Chart(sunny_by_period)
        .mark_text(dy=-10, fontWeight=600)
        .encode(
            x=alt.X("Period:N", sort=["Morning", "Afternoon", "Evening"]),
            y=alt.Y("Sunny share (%):Q"),
            text="Bar label:N",
        )
    )
    period_chart = (period_bars + period_labels).properties(height=300)
    st.altair_chart(period_chart, use_container_width=True)
    history_description = f"the last {window} days" if isinstance(window, int) else "all available dates"
    st.caption(
        f"Based on {history_description} and {provider_description}. A period counts as mostly clear when its "
        f"average cloud cover is {sunny_threshold}% or less."
    )
