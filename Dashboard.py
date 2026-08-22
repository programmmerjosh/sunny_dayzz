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
location_summary["Clear Sky (%)"] = (100 - location_summary["Cloud Cover (%)"]).round(1)
provider_pivot = latest.pivot_table(index=["Location", "Time"], columns="Source", values="Cloud Cover (%)")
provider_gap = provider_pivot.max(axis=1) - provider_pivot.min(axis=1)
provider_gap_value = provider_gap.mean()

complete_sets = {}
for entry in entries:
    key = (entry.get("location"), entry.get("overview", {}).get("date_for"))
    complete_sets.setdefault(key, set()).add(entry.get("overview", {}).get("num_of_days_between_forecast"))
coverage = sum({0, 3, 5}.issubset(leads) for leads in complete_sets.values()) / max(len(complete_sets), 1) * 100

st.markdown(
    """
    <style>
    .sunny-eyebrow {
        color: #d39213;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .sunny-intro {
        color: color-mix(in srgb, var(--text-color) 64%, transparent);
        font-size: 1rem;
        margin: 0.7rem 0 1.25rem;
    }
    .sunny-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem 1.5rem;
        margin-bottom: 1.4rem;
        color: color-mix(in srgb, var(--text-color) 68%, transparent);
        font-size: 0.88rem;
    }
    .sunny-meta strong { color: var(--text-color); }
    .sunny-trust {
        align-items: center;
        border: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
        border-radius: 14px;
        display: grid;
        gap: 1.5rem;
        grid-template-columns: minmax(0, 1fr) auto;
        margin-top: 1rem;
        padding: 1.1rem 1.25rem;
    }
    .sunny-trust-title {
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 0.25rem;
    }
    .sunny-trust-copy {
        color: color-mix(in srgb, var(--text-color) 65%, transparent);
        font-size: 0.88rem;
        line-height: 1.5;
        max-width: 760px;
    }
    .sunny-gap { min-width: 140px; text-align: right; }
    .sunny-gap strong {
        display: block;
        font-size: 1.8rem;
        letter-spacing: -0.04em;
        line-height: 1.1;
    }
    .sunny-gap span {
        color: color-mix(in srgb, var(--text-color) 58%, transparent);
        font-size: 0.75rem;
    }
    @media (max-width: 640px) {
        .sunny-trust { grid-template-columns: 1fr; gap: 0.8rem; }
        .sunny-gap { text-align: left; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="sunny-eyebrow">Latest outlook · {latest_date.strftime("%d %b %Y")}</div>', unsafe_allow_html=True)
st.title("Where is most likely to feel sunny?")
st.markdown(
    '<div class="sunny-intro">More gold means more of the sky is expected to be clear. Places are ordered from clearest to cloudiest.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <div class="sunny-meta">
        <span><strong>{frame['Location'].nunique()}</strong> locations</span>
        <span><strong>{frame['Date'].nunique()}</strong> days tracked</span>
        <span><strong>{coverage:.0f}%</strong> of 3- and 5-day forecasts available</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    heading_col, control_col = st.columns([2, 1])
    with heading_col:
        chart_heading = st.empty()
        chart_note = st.empty()
    with control_col:
        view = st.segmented_control(
            "Chart view",
            ["Clear sky", "Cloud cover"],
            default="Clear sky",
            key="dashboard_chart_view",
            label_visibility="collapsed",
        )

    if view == "Cloud cover":
        focus_column = "Cloud Cover (%)"
        focus_label = "Cloud cover"
        remainder_label = "Clear sky"
        location_order = location_summary.sort_values(focus_column, ascending=False)["Location"].tolist()
        chart_heading.subheader("Expected cloud cover")
        chart_note.caption("Longer grey bars mean more expected cloud. Places are ordered from cloudiest to clearest.")
    else:
        focus_column = "Clear Sky (%)"
        focus_label = "Clear sky"
        remainder_label = "Cloud"
        location_order = location_summary.sort_values(focus_column, ascending=False)["Location"].tolist()
        chart_heading.subheader("Expected clear sky")
        chart_note.caption("Calculated from the same cloud-cover values used throughout the dashboard.")

    chart_rows = []
    for row in location_summary.to_dict("records"):
        focus_value = row[focus_column]
        chart_rows.extend(
            [
                {
                    "Location": row["Location"],
                    "Segment": focus_label,
                    "Percentage": focus_value,
                    "Segment order": 0,
                    "Clear sky (%)": row["Clear Sky (%)"],
                    "Cloud cover (%)": row["Cloud Cover (%)"],
                },
                {
                    "Location": row["Location"],
                    "Segment": remainder_label,
                    "Percentage": 100 - focus_value,
                    "Segment order": 1,
                    "Clear sky (%)": row["Clear Sky (%)"],
                    "Cloud cover (%)": row["Cloud Cover (%)"],
                },
            ]
        )

    chart_frame = pd.DataFrame(chart_rows)
    labels = location_summary.copy()
    labels["Location label position"] = -2
    labels["Label position"] = 101
    value_suffix = "clear" if focus_label == "Clear sky" else "cloud"
    labels["Value label"] = labels[focus_column].map(lambda value: f"{value:.0f}% {value_suffix}")

    segment_colors = {
        "Clear sky": "#F4B942",
        "Cloud": "#74859A",
        "Cloud cover": "#74859A",
    }
    color_domain = [focus_label, remainder_label]
    color_range = [segment_colors[label] for label in color_domain]

    bars = (
        alt.Chart(chart_frame)
        .mark_bar(cornerRadius=5)
        .encode(
            x=alt.X(
                "Percentage:Q",
                stack="zero",
                scale=alt.Scale(domain=[-34, 118]),
                title="Share of sky (%)",
                axis=alt.Axis(values=[0, 50, 100], labelExpr="datum.value + '%'")
            ),
            y=alt.Y("Location:N", sort=location_order, title=None, axis=None),
            color=alt.Color(
                "Segment:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=alt.Legend(title=None, orient="top", direction="horizontal"),
            ),
            order=alt.Order("Segment order:Q", sort="ascending"),
            tooltip=[
                "Location:N",
                alt.Tooltip("Clear sky (%):Q", format=".1f"),
                alt.Tooltip("Cloud cover (%):Q", format=".1f"),
            ],
        )
    )
    location_labels = (
        alt.Chart(labels)
        .mark_text(align="right", baseline="middle", dx=-6, fontWeight=600, color="#8C96A5")
        .encode(
            x=alt.X(
                "Location label position:Q",
                scale=alt.Scale(domain=[-34, 118]),
                axis=None,
            ),
            y=alt.Y("Location:N", sort=location_order, axis=None),
            text="Location:N",
        )
    )
    value_labels = (
        alt.Chart(labels)
        .mark_text(align="left", baseline="middle", dx=7, fontWeight=600)
        .encode(
            x=alt.X("Label position:Q", scale=alt.Scale(domain=[-34, 118])),
            y=alt.Y("Location:N", sort=location_order, axis=None),
            text="Value label:N",
        )
    )
    chart = (bars + location_labels + value_labels).properties(height=360)
    st.altair_chart(chart, use_container_width=True)

gap_display = f"{provider_gap_value:.0f} pts" if pd.notna(provider_gap_value) else "Not available"
st.markdown(
    f"""
    <div class="sunny-trust">
        <div>
            <div class="sunny-trust-title">How certain is this outlook?</div>
            <div class="sunny-trust-copy">
                Forecast providers typically differ by {gap_display.lower()}. That makes close calls less certain,
                especially near the 35% cloud limit. This summary does not yet show whether the 3- or 5-day call was accurate.
            </div>
        </div>
        <div class="sunny-gap">
            <strong>{gap_display}</strong>
            <span>typical provider difference</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("“Same-day” is a forecast reference, not a measured weather observation.")
