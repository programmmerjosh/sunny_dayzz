import streamlit as st
import pandas as pd
import seaborn as sns

from forecast_analysis_.helpers import (
    build_discrepancy_map,
    get_discrepancies_for_date
)

# Generate red hues for visual differentiation by hour
HOUR_COLORS = {}
available_hours = [f"{h:02d}:00 UTC" for h in range(6, 21, 3)]  # Adjust as needed

palette = sns.color_palette("Reds", n_colors=20).as_hex()
palette = palette[0:len(available_hours)]  # lighter segment

for i, hour in enumerate(available_hours):
    HOUR_COLORS[hour] = palette[i]

def render_discrepancy_checker(filtered_entries, selected_location):
    st.markdown("## 🔍 Prediction Discrepancy Checker")

    if not filtered_entries:
        st.info("No forecast entries found for this location.")
        return

    # Step 1: Get discrepancy threshold from user
    with st.sidebar:
        threshold = st.slider(
            "⚙️ Discrepancy Highlight Threshold (%)",
            min_value=5,
            max_value=30,
            value=10,
            step=1
        )
    st.sidebar.caption(
        "⚠️ This slider lets you define what percentage of leniency you want before a forecast is flagged (highlighted) as a discrepancy."
    )

    # Step 2: Build grouped map
    grouped = build_discrepancy_map(filtered_entries)
    location_data = grouped.get(selected_location, {})

    if not location_data:
        st.warning(f"No forecast data found for {selected_location}")
        return

    for date_for in sorted(location_data.keys()):
        


        # Step 3: Flatten data & detect discrepancies
        source_data_by_day = location_data[date_for]
        table_data, highlights = get_discrepancies_for_date(source_data_by_day, threshold)

        # Collect all forecast ages across all sources for this date
        forecast_ages = set()
        for forecasts in source_data_by_day.values():
            for f in forecasts:
                if f.get("days_before") is not None:
                    forecast_ages.add(f"{f['days_before']}d")

        forecast_labels = ", ".join(sorted(forecast_ages, reverse=True))
        st.markdown(f"### 📅 {date_for} — Includes: {forecast_labels} forecasts")

        df = pd.DataFrame(table_data)

        # Step 4: Format for display (with highlight indicators)
        def highlight_func(row):
            key = (row["Hour"], row["Source"], row["Days Before"])
            hour = row["Hour"]
            base_color = HOUR_COLORS.get(hour, "#ffcccc")  # fallback red

            return [f"background-color: {base_color}" if key in highlights else "" for _ in row]

        styled = df.style.apply(highlight_func, axis=1)

        st.dataframe(styled, use_container_width=True)


