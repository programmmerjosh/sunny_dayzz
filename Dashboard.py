from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from cloud_cover_.data_loader import load_data
from cloud_cover_.helpers import flatten_cloud_cover
from ui import apply_theme, empty_state


SOUTHERN_HEMISPHERE_LOCATIONS = {"Port Elizabeth"}
NORTHERN_SEASONS = {
    1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring",
    5: "Spring", 6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn", 12: "Winter",
}
SOUTHERN_SEASONS = {
    1: "Summer", 2: "Summer", 3: "Autumn", 4: "Autumn",
    5: "Autumn", 6: "Winter", 7: "Winter", 8: "Winter",
    9: "Spring", 10: "Spring", 11: "Spring", 12: "Summer",
}
SEASON_MONTHS = {
    "Spring": ("March–May", "September–November"),
    "Summer": ("June–August", "December–February"),
    "Autumn": ("September–November", "March–May"),
    "Winter": ("December–February", "June–August"),
}


def local_season(location, date):
    seasons = SOUTHERN_SEASONS if location in SOUTHERN_HEMISPHERE_LOCATIONS else NORTHERN_SEASONS
    return seasons[date.month]


def build_sky_chart(summary, focus_label="Clear sky", height=360):
    if focus_label == "Cloud cover":
        focus_column = "Cloud Cover (%)"
        remainder_label = "Clear sky"
    else:
        focus_column = "Clear Sky (%)"
        remainder_label = "Cloud"

    location_order = summary.sort_values(focus_column, ascending=False)["Location"].tolist()
    chart_rows = []
    for row in summary.to_dict("records"):
        focus_value = row[focus_column]
        shared = {
            "Location": row["Location"],
            "Clear sky (%)": row["Clear Sky (%)"],
            "Cloud cover (%)": row["Cloud Cover (%)"],
            "Days": row.get("Days"),
        }
        chart_rows.extend(
            [
                {
                    **shared,
                    "Segment": focus_label,
                    "Percentage": focus_value,
                    "Segment order": 0,
                },
                {
                    **shared,
                    "Segment": remainder_label,
                    "Percentage": 100 - focus_value,
                    "Segment order": 1,
                },
            ]
        )

    chart_frame = pd.DataFrame(chart_rows)
    labels = summary.copy()
    labels["Location label position"] = -2
    labels["Label position"] = 101
    suffix = "clear" if focus_label == "Clear sky" else "cloud"
    labels["Value label"] = labels[focus_column].map(lambda value: f"{value:.0f}% {suffix}")

    segment_colors = {
        "Clear sky": "#F4B942",
        "Cloud": "#74859A",
        "Cloud cover": "#74859A",
    }
    color_domain = [focus_label, remainder_label]
    tooltip = [
        "Location:N",
        alt.Tooltip("Clear sky (%):Q", format=".1f"),
        alt.Tooltip("Cloud cover (%):Q", format=".1f"),
    ]
    if "Days" in summary.columns:
        tooltip.append(alt.Tooltip("Days:Q", format=",d", title="Same-day dates"))

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
                scale=alt.Scale(
                    domain=color_domain,
                    range=[segment_colors[label] for label in color_domain],
                ),
                legend=alt.Legend(title=None, orient="top", direction="horizontal"),
            ),
            order=alt.Order("Segment order:Q", sort="ascending"),
            tooltip=tooltip,
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
    return (bars + location_labels + value_labels).properties(height=height)


st.set_page_config(page_title="Sunny Dayzz", page_icon="☀️", layout="wide")
apply_theme()

entries = load_data(Path(__file__).parent / "data" / "cloud_cover.json")
if not entries:
    empty_state("No weather data has been collected yet.")

same_day = [entry for entry in entries if entry.get("overview", {}).get("num_of_days_between_forecast") == 0]
frame = pd.DataFrame([row for entry in same_day for row in flatten_cloud_cover(entry)]).dropna(subset=["Cloud Cover (%)"])
if frame.empty:
    empty_state()

# Average providers and daytime readings first so every date contributes equally.
daily = frame.groupby(["Location", "Date"], as_index=False)["Cloud Cover (%)"].mean()
daily["Clear Sky (%)"] = 100 - daily["Cloud Cover (%)"]
daily["Local season"] = [local_season(row.Location, row.Date) for row in daily.itertuples()]

latest_date = frame["Date"].max()
latest = frame[frame["Date"] == latest_date]
latest_summary = latest.groupby("Location", as_index=False)["Cloud Cover (%)"].mean().round(1)
latest_summary["Clear Sky (%)"] = (100 - latest_summary["Cloud Cover (%)"]).round(1)

provider_pivot = frame.pivot_table(
    index=["Location", "Date", "Time"],
    columns="Source",
    values="Cloud Cover (%)",
)
provider_counts = provider_pivot.notna().sum(axis=1)
provider_gaps = (provider_pivot.max(axis=1) - provider_pivot.min(axis=1))[provider_counts >= 2]
provider_gaps = provider_gaps.rename("Provider gap").reset_index()
provider_gaps["Local season"] = [local_season(row.Location, row.Date) for row in provider_gaps.itertuples()]

complete_sets = {}
for entry in entries:
    key = (entry.get("location"), entry.get("overview", {}).get("date_for"))
    complete_sets.setdefault(key, set()).add(entry.get("overview", {}).get("num_of_days_between_forecast"))
coverage = sum({0, 3, 5}.issubset(leads) for leads in complete_sets.values()) / max(len(complete_sets), 1) * 100

today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
data_age_days = max((today - latest_date.normalize()).days, 0)
if data_age_days == 0:
    freshness_text = "Data includes today"
elif data_age_days == 1:
    freshness_text = "Data is 1 day behind today"
else:
    freshness_text = f"Data is {data_age_days} days behind today"

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
        margin: 1rem 0 1.2rem;
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

st.markdown(
    f'<div class="sunny-eyebrow">Historical forecast patterns · Data through {latest_date.strftime("%d %b %Y")}</div>',
    unsafe_allow_html=True,
)
st.title("Where has typically had the clearest sky?")
st.markdown(
    '<div class="sunny-intro">Compare the average clear-sky outlook for each location during its own local season. More gold means clearer skies.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <div class="sunny-meta">
        <span><strong>{frame['Location'].nunique()}</strong> locations</span>
        <span><strong>{frame['Date'].nunique()}</strong> days tracked</span>
        <span><strong>{coverage:.0f}%</strong> of 3- and 5-day forecasts available</span>
        <span><strong>{freshness_text}</strong></span>
    </div>
    """,
    unsafe_allow_html=True,
)

season_options = ["Spring", "Summer", "Autumn", "Winter", "All year"]
current_season = NORTHERN_SEASONS[today.month]

with st.container(border=True):
    heading_col, season_col, view_col = st.columns([2, 1, 1])
    with season_col:
        selected_season = st.selectbox(
            "Local season",
            season_options,
            index=season_options.index(current_season),
            key="dashboard_season",
        )
    with view_col:
        view = st.segmented_control(
            "Chart view",
            ["Clear sky", "Cloud cover"],
            default="Clear sky",
            key="dashboard_chart_view",
        )

    selected_daily = daily if selected_season == "All year" else daily[daily["Local season"] == selected_season]
    historical_summary = (
        selected_daily.groupby("Location", as_index=False)
        .agg(
            **{
                "Cloud Cover (%)": ("Cloud Cover (%)", "mean"),
                "Days": ("Date", "nunique"),
            }
        )
        .round({"Cloud Cover (%)": 1})
    )
    historical_summary["Clear Sky (%)"] = (100 - historical_summary["Cloud Cover (%)"]).round(1)

    with heading_col:
        if view == "Cloud cover":
            st.subheader(f"Typical cloud cover · {selected_season.lower()}")
            st.caption("Longer grey bars mean more forecast cloud. Places are ordered from cloudiest to clearest.")
        else:
            st.subheader(f"Typical clear sky · {selected_season.lower()}")
            st.caption("Each date counts equally before the seasonal average is calculated.")

    if selected_season == "All year":
        st.caption("All available same-day forecast dates are included for every location.")
    else:
        northern_months, southern_months = SEASON_MONTHS[selected_season]
        st.caption(
            f"{selected_season} means {northern_months} in the Northern Hemisphere and "
            f"{southern_months} in the Southern Hemisphere. Port Elizabeth uses the Southern Hemisphere season."
        )

    st.altair_chart(build_sky_chart(historical_summary, focus_label=view), use_container_width=True)
    min_days = int(historical_summary["Days"].min())
    max_days = int(historical_summary["Days"].max())
    day_range = f"{min_days} days" if min_days == max_days else f"{min_days}–{max_days} days"
    st.caption(f"Based on {day_range} of same-day forecasts per location for this selection.")

selected_gap_rows = provider_gaps if selected_season == "All year" else provider_gaps[provider_gaps["Local season"] == selected_season]
provider_gap_value = selected_gap_rows["Provider gap"].mean()
gap_display = f"{provider_gap_value:.0f} pts" if pd.notna(provider_gap_value) else "Not available"
st.markdown(
    f"""
    <div class="sunny-trust">
        <div>
            <div class="sunny-trust-title">How consistent are these forecasts?</div>
            <div class="sunny-trust-copy">
                During the selected period, providers differed by {gap_display.lower()} on average.
                Close calls near the 35% cloud limit are therefore less certain. This measures provider agreement,
                not whether the forecast matched observed weather.
            </div>
        </div>
        <div class="sunny-gap">
            <strong>{gap_display}</strong>
            <span>average provider difference</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander(f"Most recently available outlook · {latest_date.strftime('%d %b %Y')}"):
    st.caption(f"{freshness_text}. Values average both providers and five daytime forecasts for this single date.")
    st.altair_chart(build_sky_chart(latest_summary, focus_label="Clear sky", height=300), use_container_width=True)

st.caption("These are averages of same-day forecasts, not measured weather observations.")
