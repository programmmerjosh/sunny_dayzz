import streamlit as st
import os
import pandas as pd

from dashboard_.helpers import is_sunny
from dashboard_.data_loader import load_data, get_filtered_data
from dashboard_.charts import build_timeline_chart, build_pie_chart
from dashboard_.views import render_discrepancy_checker, render_forecast_accuracy

COLOR_SCHEME = {
    "Morning": "#d3d3d3",    # Light grey   # alternative: "Morning": "#a6c8ff",    # Light sky blue
    "Afternoon": "#a9a9a9",  # Medium grey   # alternative: "Afternoon": "#5a9bd5",  # Mid blue-grey
    "Evening": "#696969"     # Dark grey   # alternative: "Evening": "#2e3b4e"     # Dark twilight blue
}

st.set_page_config(page_title="Sunny Dayzz", layout="wide")
st.title("🌞 Sunny Dayzz Dashboard")
st.text("NOTE: the Cloud Cover Trend graph cannot be accurate until we manage to acquire more data over a substancial amount of time."
"\nDate we started collecting data for this project: 02 April 2025")

# DATA_PATH = os.path.join("data", "weather_data.json") # old data location
DATA_PATH = os.path.join("data", "cloud_cover.json") # real data
# DATA_PATH = os.path.join("data", "dummy_data.json") # dummy data
data = load_data(DATA_PATH)

if not data:
    st.error("No weather data found.")
    st.stop()

locations = sorted(set(entry["location"] for entry in data))
selected_location = st.sidebar.selectbox("Select a location", locations)
filtered = get_filtered_data(data, selected_location)

# 📈 Timeline Chart
timeline_data = []
for entry in filtered:
    date = pd.to_datetime(entry["date_for"], format="%d/%m/%Y")  # 💥 Convert to datetime here
    cloud_cover = {
        time.title(): int(value.strip('%'))  # Make sure keys are title case
        for time, value in entry["cloud_cover"].items()
    }
    for time_of_day, percent in cloud_cover.items():
        timeline_data.append({
            "Date": date,
            "Time of Day": time_of_day,
            "Cloud Cover (%)": percent
        })

df_timeline = pd.DataFrame(timeline_data)

# display the number of date entries we have in our dataset
st.write("📅 Unique Dates in Timeline:", df_timeline["Date"].nunique())

st.markdown("## 📈 Cloud Cover Trend")
st.altair_chart(build_timeline_chart(df_timeline, COLOR_SCHEME), use_container_width=True)

# ☀️ Sunny vs Cloudy Pie
zero_day = [e for e in filtered if e["days_before"] == 0]
sunny_days = [e for e in zero_day if is_sunny(e["cloud_cover"])]
cloudy_days = [e for e in zero_day if not is_sunny(e["cloud_cover"])]

st.markdown("## ☀️ Sunny vs Cloudy Days (Based on 0-Day Predictions)")

st.metric("Total Days", len(zero_day))
st.metric("☀️ Sunny Days", len(sunny_days))
st.metric("🌥️ Cloudy Days", len(cloudy_days))

st.altair_chart(build_pie_chart(sunny_days, cloudy_days), use_container_width=True)

# 🔍 Discrepancy Checker
prediction_map = render_discrepancy_checker(filtered)

# 📊 Forecast Accuracy
render_forecast_accuracy(prediction_map)
