import streamlit as st
import json
import os
import pandas as pd
import altair as alt

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
    st.subheader(f'📅 {entry["prediction_date"]} ({entry["days_before"]} days before)')
    cols = st.columns(2)

    with cols[0]:
        st.markdown("**☀️ Summary**")
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
            y=alt.Y("Cloud Cover (%):Q"),
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
