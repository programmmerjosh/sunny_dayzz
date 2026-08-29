from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from forecast_analysis_.helpers import build_comparison_dataframe, load_forecast_data
from ui import apply_theme, empty_state

st.set_page_config(page_title="Forecast drift", page_icon="📈", layout="wide")
apply_theme()

data_path = Path(__file__).parents[1] / "data" / "cloud_cover.json"
data = load_forecast_data(data_path)
comparisons = build_comparison_dataframe(data)
if comparisons.empty:
    empty_state("There are no complete 0-, 3-, and 5-day forecast sets to compare yet.")

locations = sorted(comparisons["Location"].unique())
with st.sidebar:
    selected_location = st.selectbox("Location", locations)
    history = st.selectbox("History", [30, 90, 180, "All"], index=1, format_func=lambda value: f"Last {value} days" if isinstance(value, int) else value)
    tolerance = st.slider("Close enough (percentage points)", 5, 30, 10)

frame = comparisons[comparisons["Location"] == selected_location].copy()
if isinstance(history, int):
    cutoff = frame["Date"].max() - pd.Timedelta(days=history - 1)
    frame = frame[frame["Date"] >= cutoff]
if frame.empty:
    empty_state()

frame["Within tolerance"] = frame["Absolute difference (pp)"] <= tolerance
by_lead = frame.groupby("Days before")["Absolute difference (pp)"].mean()
mae_3 = by_lead.get(3, float("nan"))
mae_5 = by_lead.get(5, float("nan"))

st.title(f"📈 Forecast drift · {selected_location}")
st.caption("How far 3- and 5-day forecasts moved before the same-day outlook. Lower is steadier.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("3-day drift", f"{mae_3:.1f} pts")
col2.metric("5-day drift", f"{mae_5:.1f} pts")
col3.metric("Close calls", f"{frame['Within tolerance'].mean() * 100:.0f}%")
col4.metric("Comparisons", f"{len(frame):,}")

with st.container(border=True):
    st.markdown("**How these figures are counted**")
    st.markdown(
        f"- **Close calls:** Percentage of individual comparisons where the earlier forecast stayed within "
        f"{tolerance} percentage points of the same-day forecast.\n"
        "- **Comparison:** One provider, target date and forecast time, comparing either its 3- or 5-day "
        "forecast with its same-day forecast. A single date can contribute multiple comparisons."
    )

summary = (
    frame.groupby(["Source", "Lead time"], as_index=False)
    .agg(
        **{
            "Mean drift (pp)": ("Absolute difference (pp)", "mean"),
            "Close calls (%)": ("Within tolerance", "mean"),
        }
    )
)
summary["Close calls (%)"] *= 100

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Drift by provider")
    st.caption("By how much did forecasts typically change?")
    ranking = (
        alt.Chart(summary)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X("Mean drift (pp):Q", title="Mean absolute change (points)"),
            y=alt.Y("Source:N", title=None),
            color=alt.Color("Lead time:N", scale=alt.Scale(domain=["3 days", "5 days"], range=["#F4B942", "#52677F"]), title=None),
            yOffset="Lead time:N",
            tooltip=["Source", "Lead time", alt.Tooltip("Mean drift (pp):Q", format=".1f")],
        )
        .properties(height=260)
    )
    st.altair_chart(ranking, use_container_width=True)
with right:
    st.subheader("Within tolerance")
    st.caption("How often was that change small enough to count as close?")
    agreement = (
        alt.Chart(summary)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Source:N", title=None),
            y=alt.Y("Close calls (%):Q", scale=alt.Scale(domain=[0, 100]), title=f"Within ±{tolerance} points (%)"),
            color=alt.Color("Lead time:N", scale=alt.Scale(domain=["3 days", "5 days"], range=["#F4B942", "#52677F"]), title=None),
            xOffset="Lead time:N",
            tooltip=["Source", "Lead time", alt.Tooltip("Close calls (%):Q", format=".0f")],
        )
        .properties(height=260)
    )
    st.altair_chart(agreement, use_container_width=True)

st.subheader("How drift changed over time")
daily = frame.groupby(["Date", "Lead time"], as_index=False)["Absolute difference (pp)"].mean()
daily = daily.sort_values("Date")
daily["14-day average"] = daily.groupby("Lead time")["Absolute difference (pp)"].transform(lambda series: series.rolling(14, min_periods=3).mean())
trend = (
    alt.Chart(daily.dropna(subset=["14-day average"]))
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("Date:T", title=None),
        y=alt.Y("14-day average:Q", title="14-day average drift (points)"),
        color=alt.Color("Lead time:N", scale=alt.Scale(domain=["3 days", "5 days"], range=["#F4B942", "#52677F"]), title=None),
        tooltip=[alt.Tooltip("Date:T", format="%d %b %Y"), "Lead time", alt.Tooltip("14-day average:Q", format=".1f")],
    )
    .properties(height=300)
)
st.altair_chart(trend, use_container_width=True)


available_dates = sorted(frame["Date"].dt.date.unique())
available_date_set = set(available_dates)
calendar_scope = f"{selected_location}|{history}"

if st.session_state.get("forecast_calendar_scope") != calendar_scope:
    st.session_state["forecast_calendar_scope"] = calendar_scope
    st.session_state["forecast_date_picker"] = available_dates[-1]

if st.session_state.get("forecast_date_picker") not in available_date_set:
    st.session_state["forecast_date_picker"] = available_dates[-1]

st.subheader("Inspect a date")
st.caption("Choose a date with complete comparison data.")

selected_date = st.date_input(
    "Date",
    min_value=available_dates[0],
    max_value=available_dates[-1],
    key="forecast_date_picker",
    format="DD/MM/YYYY",
    label_visibility="collapsed",
)

if selected_date not in available_date_set:
    st.warning(
        "There is no complete comparison data for this date. "
        "Please choose another date."
    )
    st.stop()
    
selected = frame[frame["Date"].dt.date == selected_date].copy()
    
long = pd.concat(
    [
        selected[["Hour", "Source", "Same-day cloud (%)"]].drop_duplicates().rename(columns={"Same-day cloud (%)": "Cloud cover (%)"}).assign(Outlook="Same day"),
        selected[["Hour", "Source", "Lead time", "Forecast cloud (%)"]].rename(columns={"Lead time": "Outlook", "Forecast cloud (%)": "Cloud cover (%)"}),
    ],
    ignore_index=True,
)
detail = (
    alt.Chart(long)
    .mark_line(point=True, strokeWidth=2.5)
    .encode(
        x=alt.X("Hour:O", title="UTC"),
        y=alt.Y("Cloud cover (%):Q", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Outlook:N", scale=alt.Scale(domain=["Same day", "3 days", "5 days"], range=["#F4B942", "#65A6A4", "#52677F"]), title=None),
        tooltip=["Source", "Outlook", "Hour", "Cloud cover (%)"],
    )
    .properties(height=230)
    .facet(row=alt.Row("Source:N", title=None))
)
st.altair_chart(detail, use_container_width=True)
st.caption("Same-day values are provider forecasts used as the reference; they are not observations from a weather station.")
