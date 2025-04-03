import streamlit as st
import json
import os
import pandas as pd
import altair as alt
from collections import defaultdict

def is_sunny(cloud_cover_dict):
    """Return True if all time blocks are ≤ 20% cloud cover."""
    try:
        values = [int(v.strip('%')) for v in cloud_cover_dict.values()]
        return all(v <= 20 for v in values)
    except Exception:
        return False
    
def compare_cloud_cover(predicted, actual, tolerance=10):
    """
    Compare predicted vs actual cloud cover.
    Returns number of matching time blocks (out of 3).
    """
    matches = 0
    for time in ["Morning", "Afternoon", "Evening"]:
        try:
            pred_val = int(predicted[time].strip('%'))
            actual_val = int(actual[time].strip('%'))
            if abs(pred_val - actual_val) <= tolerance:
                matches += 1
        except Exception:
            continue
    return matches

# 🎨 Custom color scheme (editable anytime!)
# COLOR_SCHEME = {
#     "Morning": "#a6c8ff",    # Light sky blue
#     "Afternoon": "#5a9bd5",  # Mid blue-grey
#     "Evening": "#2e3b4e"     # Dark twilight blue
# }

COLOR_SCHEME = {
    "Morning": "#d3d3d3",    # Light grey
    "Afternoon": "#a9a9a9",  # Medium grey
    "Evening": "#696969"     # Dark grey
}

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

timeline_data = []

for entry in filtered:
    date = pd.to_datetime(entry["prediction_date"], format="%d/%m/%Y")  # 💥 Convert to datetime here
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
df_timeline["Date"] = pd.to_datetime(df_timeline["Date"], format="%d/%m/%Y")

# display the number of date entries we have in our dataset
st.write("📅 Unique Dates in Timeline:", df_timeline["Date"].nunique())

st.markdown("## 📈 Cloud Cover Trend")
timeline_chart = alt.Chart(df_timeline).mark_line(point=True).encode(
    x=alt.X("Date:T", title="Date"),
    y=alt.Y("Cloud Cover (%):Q"),
    color=alt.Color("Time of Day:N",
                    sort=list(COLOR_SCHEME.keys()),
                    scale=alt.Scale(
                        domain=list(COLOR_SCHEME.keys()),
                        range=list(COLOR_SCHEME.values())
                    )),
    tooltip=["Date", "Time of Day", "Cloud Cover (%)"],
    detail="Time of Day:N"  # 👈 Ensures each time-of-day series gets its own line
).properties(
    width="container",
    height=300
)

st.altair_chart(timeline_chart, use_container_width=True)

st.text("NOTE: The (# Days before) indicates the number of days before the given date that the weather prediction was made")

# Display entries
for entry in filtered:
    sunny_icon = " ☀️" if is_sunny(entry["cloud_cover"]) else ""
    st.subheader(f'📅 {entry["prediction_date"]} ({entry["days_before"]} days before){sunny_icon}')
    cols = st.columns(2)

    with cols[0]:
        st.markdown("**Data Summary**")
        st.write(entry["summary"])

    with cols[1]:
        st.markdown("**☁️ Cloud Cover**")
        
        # Convert cloud cover values (like "30%") to integers
        cloud_cover = {
            time.title(): int(value.replace('%', '').strip())
            for time, value in entry["cloud_cover"].items()
        }

        # Build DataFrame
        df = pd.DataFrame({
            "Time of Day": list(cloud_cover.keys()),
            "Cloud Cover (%)": list(cloud_cover.values())
        })

        time_order = ["Morning", "Afternoon", "Evening"]

        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Time of Day:N", sort=time_order),
            y=alt.Y("Cloud Cover (%):Q", scale=alt.Scale(domain=[0, 100]), title="Cloud Cover (%)"),
            color=alt.Color("Time of Day:N",
                            sort=time_order,
                            scale=alt.Scale(
                                domain=list(COLOR_SCHEME.keys()),
                                range=list(COLOR_SCHEME.values())
                            ))
        ).properties(
            width=250,
            height=200
        )

        st.altair_chart(chart.interactive(), use_container_width=True)

    if entry.get("discrepancies") and entry["discrepancies"].lower() != "n/a":
        st.markdown("**⚠️ Discrepancies**")
        st.warning(entry["discrepancies"])

    st.markdown("---")

# Prediction Discrepancy Checker
st.markdown("## 🔍 Prediction Discrepancy Checker")

# Group entries by predicted date
prediction_map = defaultdict(dict)

seven_day_scores = []
three_day_scores = []
total_possible = 0

for pred_date, predictions in prediction_map.items():
    if all(day in predictions for day in [0, 3, 7]):
        actual = predictions[0]["cloud_cover"]
        total_possible += 3  # 3 time blocks

        # 7-day forecast accuracy
        score7 = compare_cloud_cover(predictions[7]["cloud_cover"], actual)
        seven_day_scores.append(score7)

        # 3-day forecast accuracy
        score3 = compare_cloud_cover(predictions[3]["cloud_cover"], actual)
        three_day_scores.append(score3)

for entry in filtered:
    prediction_date = entry["prediction_date"]
    days_before = entry["days_before"]
    prediction_map[prediction_date][days_before] = entry

for pred_date, predictions in prediction_map.items():
    if all(day in predictions for day in [0, 3, 7]):
        with st.expander(f"📅 {pred_date} - Compare Predictions (7 vs 3 vs 0 Days Before)"):
            cols = st.columns(3)
            for i, day in enumerate([7, 3, 0]):
                with cols[i]:
                    entry = predictions[day]
                    st.markdown(f"**{day} Days Before**")
                    st.markdown("☀️ **Summary**")
                    st.write(entry["summary"])
                    st.markdown("☁️ **Cloud Cover**")
                    st.write(entry["cloud_cover"])
                    if entry.get("discrepancies") and entry["discrepancies"].lower() != "n/a":
                        st.warning(f'Discrepancy: {entry["discrepancies"]}')

# Sunny vs Cloudy Ratio
zero_day_entries = [e for e in filtered if e["days_before"] == 0]
sunny_days = [e for e in zero_day_entries if is_sunny(e["cloud_cover"])]
cloudy_days = [e for e in zero_day_entries if not is_sunny(e["cloud_cover"])]

st.markdown("## ☀️ Sunny vs Cloudy Days (Based on 0-Day Predictions)")

st.metric("Total Days", len(zero_day_entries))
st.metric("☀️ Sunny Days", len(sunny_days))
st.metric("🌥️ Cloudy Days", len(cloudy_days))

# Pie chart
summary_df = pd.DataFrame({
    "Type": ["Sunny", "Cloudy"],
    "Count": [len(sunny_days), len(cloudy_days)]
})

pie = alt.Chart(summary_df).mark_arc(innerRadius=50).encode(
    theta="Count:Q",
    color="Type:N"
).properties(
    width=300,
    height=300
)

st.altair_chart(pie, use_container_width=True)

total_7 = sum(seven_day_scores)
total_3 = sum(three_day_scores)

accuracy_7 = round((total_7 / total_possible) * 100, 2) if total_possible > 0 else 0
accuracy_3 = round((total_3 / total_possible) * 100, 2) if total_possible > 0 else 0

st.markdown("## 📊 Forecast Accuracy (vs 0-Day Actuals)")
st.metric("7-Day Forecast Accuracy", f"{accuracy_7}%")
st.metric("3-Day Forecast Accuracy", f"{accuracy_3}%")
