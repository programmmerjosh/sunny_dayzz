import streamlit as st
import os
import pandas as pd

from cloud_cover_.helpers import is_sunny_day, flatten_cloud_cover, get_sunny_blocks, get_combined_block_averages
from cloud_cover_.data_loader import load_data, get_filtered_data
from cloud_cover_.charts import build_pie_chart, build_time_chart

st.set_page_config(page_title="Sunny Dayzz", layout="wide")
st.title("☁️ Cloud Cover")
st.text("NOTE: Our charts only show 0-day (on-the-day) forecasts and not future predictions")

DATA_PATH = os.path.join("data", "cloud_cover.json")
data = load_data(DATA_PATH)

if not data:
    st.error("No weather data found.")
    st.stop()

locations = sorted(set(entry["location"] for entry in data))
selected_location = st.sidebar.selectbox("Select a location", locations)
filtered = get_filtered_data(data, selected_location)

actuals_only = [
    e for e in filtered
    if e["overview"]["num_of_days_between_forecast"] == 0
]

if not actuals_only:
    st.warning("⚠️ No 0-day (actual) forecast data available yet for this location.")
    st.stop()

# ========== 📈 Timeline Charts ============# 
timeline_data = []
for entry in actuals_only:
    timeline_data.extend(flatten_cloud_cover(entry))

# dataframe timeline
df_timeline = pd.DataFrame(timeline_data)
df_timeline["Date"] = pd.to_datetime(df_timeline["Date"])
df_timeline["Cloud Cover (%)"] = df_timeline["Cloud Cover (%)"].astype(int)
df_timeline["Tooltip Label"] = df_timeline["Cloud Cover (%)"].apply(lambda x: f"{x}%" if x is not None else "—")

# display the number of date entries we have in our dataset
st.write("📅 Unique Dates in Timeline:", df_timeline["Date"].nunique())

# chart 1 title
st.markdown("## ☁️ Cloud Cover by Source")

# display chart 1
st.altair_chart(build_time_chart(df_timeline, facet_by_date=True), use_container_width=True)

# Unique options from your dataframe
available_dates = sorted(set(e["overview"]["date_for"] for e in actuals_only))
available_sources = sorted(df_timeline["Source"].unique())

# Sidebar filters
selected_date = st.sidebar.selectbox("Select a date to filter cloud cover trends", available_dates)
selected_sources = st.sidebar.multiselect(
    "Select weather data sources to filter", available_sources, default=available_sources
)

filtered_df = df_timeline[
    (df_timeline["Date"].dt.strftime("%d/%m/%Y") == selected_date) &
    (df_timeline["Source"].isin(selected_sources))
].copy()

# chart 2 title
st.markdown("## ☁️ Cloud Cover Trend (Filtered)")

# display chart 2
st.altair_chart(build_time_chart(filtered_df), use_container_width=True)

# set threshold for sunny day/time-block
sunny_threshold = st.sidebar.slider(
    "Define cloudy threshold (%)", 20, 65, 35,
)
st.sidebar.caption(
    "☀️ This slider lets you define what percentage of cloud cover for any particular day/time-period you still clasify as 'sunny'.\n"
    "A lower threshold means you're more strict (e.g., setting it to 20% means that 21% cloud cover for any day would count as a cloudy day),\n"
    "while a higher threshold allows for more clouds in your 'sunny' days/mornings/afternoons/evenings."
)

selected_block = st.sidebar.radio(
    "Select time block to view (for block pie chart)",
    ["morning", "afternoon", "evening"],
)

# get sunny days pie chart
zero_day = [
    e for e in filtered
    if e["overview"]["num_of_days_between_forecast"] == 0
]

sunny_days = []
cloudy_days = []

for entry in zero_day:
    block_averages = get_combined_block_averages(entry, selected_sources)

    if is_sunny_day(block_averages, sunny_threshold):
        sunny_days.append(entry)
    else:
        cloudy_days.append(entry)

st.markdown("## ☀️ Sunny vs Cloudy Days")

st.metric("Total Days", len(zero_day))
st.metric("☀️ Sunny Days", len(sunny_days))
st.metric("🌥️ Cloudy Days", len(cloudy_days))

st.altair_chart(build_pie_chart(sunny_days, cloudy_days, use_len=True), use_container_width=True)

# get sunny time-block pie chart
sunny_blocks = 0
cloudy_blocks = 0

for entry in zero_day:
    block_averages = get_combined_block_averages(entry, selected_sources)
    block_status = get_sunny_blocks(block_averages, sunny_threshold)

    # This is where you use it:
    is_block_sunny = block_status.get(selected_block)

    if is_block_sunny is True:
        sunny_blocks += 1
    elif is_block_sunny is False:
        cloudy_blocks += 1


st.markdown(f"## 🌤️ Sunny vs Cloudy ({selected_block.capitalize()}s Only)")

st.metric("☀️ Sunny Blocks", sunny_blocks)
st.metric("🌥️ Cloudy Blocks", cloudy_blocks)

st.altair_chart(build_pie_chart(sunny_blocks, cloudy_blocks), use_container_width=True)