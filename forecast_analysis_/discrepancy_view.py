import streamlit as st
import pandas as pd
import seaborn as sns
from datetime import datetime

from forecast_analysis_.helpers import (
    build_discrepancy_map,
    get_discrepancies_for_date
)

# 🎨 Generate red hues for visual differentiation by hour
HOUR_COLORS = {}
available_hours = [f"{h:02d}:00 UTC" for h in range(6, 21, 3)]  # Adjust as needed
palette = sns.color_palette("Reds", n_colors=20).as_hex()
palette = palette[:len(available_hours)]

for i, hour in enumerate(available_hours):
    HOUR_COLORS[hour] = palette[i]

def render_discrepancy_checker(filtered_entries, selected_location):
    st.markdown("## 🔍 Prediction Discrepancy Checker")

    if not filtered_entries:
        st.info("No forecast entries found for this location.")
        return

    # Step 1: Build grouped map
    grouped = build_discrepancy_map(filtered_entries)
    location_data = grouped.get(selected_location, {})

    if not location_data:
        st.warning(f"No forecast data found for {selected_location}")
        return

    # --- Prepare date handling
    available_date_strs = sorted(location_data.keys(), reverse=True)
    available_dates = [datetime.strptime(d, "%d/%m/%Y") for d in available_date_strs]
    date_map = dict(zip(available_dates, available_date_strs))  # datetime → string

    # --- Sidebar controls
    with st.sidebar:
        threshold = st.slider(
            "⚙️ Discrepancy Highlight Threshold (%)",
            min_value=5,
            max_value=30,
            value=10,
            step=1,
            key="discrepancy_threshold_slider"
        )
        st.caption("⚠️ This slider lets you define what percentage of leniency you want before a forecast is flagged (highlighted) as a discrepancy.")

        use_range = st.checkbox("📆 Use custom date range", value=False)

        if use_range:
            min_d, max_d = min(available_dates), max(available_dates)
            selected_range = st.date_input(
                "Select forecast date range",
                value=(max_d, max_d),
                min_value=min_d,
                max_value=max_d,
                format="DD/MM/YYYY"
            )

            if isinstance(selected_range, tuple) and len(selected_range) == 2:
                filtered_keys = [
                    date_map[d] for d in available_dates
                    if selected_range[0] <= d.date() <= selected_range[1]
                ]
            else:
                filtered_keys = []
        else:
            filtered_keys = available_date_strs[:3]  # Default: last 3

        selected_ages = st.multiselect(
            "🕒 Show forecasts for:",
            options=["0d", "3d", "5d"],
            default=["0d", "3d", "5d"]
        )

    if not filtered_keys:
        st.info("No forecast entries for the selected date range.")
        return

    # Step 2: Loop through selected forecast dates
    for date_for in filtered_keys:
        source_data_by_day = location_data[date_for]
        table_data, highlights = get_discrepancies_for_date(
            source_data_by_day,
            threshold,
            filter_days=selected_ages
        )

        # 🚫 Skip this date if no entries match the selected forecast ages
        if not table_data:
            continue

        # Show which days_before are included
        forecast_ages = set()
        for forecasts in source_data_by_day.values():
            for f in forecasts:
                if f.get("days_before") is not None:
                    forecast_ages.add(f"{f['days_before']}d")

        forecast_labels = ", ".join(sorted(forecast_ages, reverse=True))
        st.markdown(f"### 📅 {date_for} — Includes: {forecast_labels} forecasts")

        df = pd.DataFrame(table_data)

        # Step 3: Style rows with hour-based color highlighting
        def highlight_func(row):
            key = (row["Hour"], row["Source"], row["Days Before"])
            hour = row["Hour"]
            base_color = HOUR_COLORS.get(hour, "#ffcccc")
            return [f"background-color: {base_color}; color: black" if key in highlights else "" for _ in row]

        styled = df.style.apply(highlight_func, axis=1)
        st.dataframe(styled, use_container_width=True)

        return threshold
