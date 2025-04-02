import streamlit as st
import json
import os
import pandas as pd
import altair as alt

# Load data
DATA_PATH = os.path.join("data", "weather_data.json")

if not os.path.exists(DATA_PATH):
    st.error("No weather data found.")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

st.set_page_config(page_title="Sunny Dayzz Dashboard", layout="wide")

st.title("🌞 Sunny Dayzz Forecast Dashboard")
st.text("NOTE: the Cloud Cover Trend graph cannot be accurate until we manage to acquire more data over a substancial amount of time."
"\nDate we started collecting data for this project: 02 April 2025")

# Sidebar filters
locations = sorted(set(entry["location"] for entry in data))
selected_location = st.sidebar.selectbox("Select a location", locations)

# Filter data
filtered = [entry for entry in data if entry["location"] == selected_location]

# Sort by date
filtered.sort(key=lambda x: x["prediction_date"])

# 📊 Build combined cloud cover timeline chart
timeline_data = []

for entry in filtered:
    date = entry["prediction_date"]
    cloud_cover = {
        time: int(value.strip('%'))
        for time, value in entry["cloud_cover"].items()
    }
    for time_of_day, percent in cloud_cover.items():
        timeline_data.append({
            "Date": date,
            "Time of Day": time_of_day,
            "Cloud Cover (%)": percent
        })

df_timeline = pd.DataFrame(timeline_data)

st.markdown("## 📈 Cloud Cover Trend")
timeline_chart = alt.Chart(df_timeline).mark_line(point=True).encode(
    x="Date:T",
    y="Cloud Cover (%):Q",
    color="Time of Day:N",
    tooltip=["Date", "Time of Day", "Cloud Cover (%)"]
).properties(
    width="container",
    height=300
)

st.altair_chart(timeline_chart, use_container_width=True)


# Display entries
for entry in filtered:
    st.subheader(f'📅 {entry["prediction_date"]} ({entry["days_before"]} days before)')
    cols = st.columns(2)

    with cols[0]:
        st.markdown("**☀️ Summary**")
        st.write(entry["summary"])



    with cols[1]:
        st.markdown("**☁️ Cloud Cover**")
        
        # Convert cloud cover values (like "30%") to integers
        cloud_cover = {
            time: int(value.strip('%'))
            for time, value in entry["cloud_cover"].items()
        }

        # Build DataFrame
        df = pd.DataFrame({
            "Time of Day": list(cloud_cover.keys()),
            "Cloud Cover (%)": list(cloud_cover.values())
        })

        # Plot with Altair
        chart = alt.Chart(df).mark_bar().encode(
            x="Time of Day",
            y="Cloud Cover (%)",
            color="Time of Day"
        ).properties(
            width=250,
            height=200
        )

        st.altair_chart(chart, use_container_width=True)


    if entry.get("discrepancies") and entry["discrepancies"].lower() != "n/a":
        st.markdown("**⚠️ Discrepancies**")
        st.warning(entry["discrepancies"])

    st.markdown("---")
