import streamlit as st
import json
import os

# Load data
DATA_PATH = os.path.join("data", "weather_data.json")

if not os.path.exists(DATA_PATH):
    st.error("No weather data found.")
    st.stop()

with open(DATA_PATH, "r") as f:
    data = json.load(f)

st.set_page_config(page_title="Sunny Dayzz Dashboard", layout="wide")

st.title("🌞 Sunny Dayzz Forecast Dashboard")

# Sidebar filters
locations = sorted(set(entry["location"] for entry in data))
selected_location = st.sidebar.selectbox("Select a location", locations)

# Filter data
filtered = [entry for entry in data if entry["location"] == selected_location]

# Sort by date
filtered.sort(key=lambda x: x["prediction_date"])

# Display entries
for entry in filtered:
    st.subheader(f'📅 {entry["prediction_date"]} ({entry["days_before"]} days before)')
    cols = st.columns(2)

    with cols[0]:
        st.markdown("**☀️ Summary**")
        st.write(entry["summary"])

    with cols[1]:
        st.markdown("**☁️ Cloud Cover**")
        st.write(entry["cloud_cover"])

    if entry.get("discrepancies") and entry["discrepancies"].lower() != "n/a":
        st.markdown("**⚠️ Discrepancies**")
        st.warning(entry["discrepancies"])

    st.markdown("---")
