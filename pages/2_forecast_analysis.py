import streamlit as st

from forecast_analysis_.helpers import evaluate_source_accuracy, load_forecast_data
from forecast_analysis_.discrepancy_view import render_discrepancy_checker

st.set_page_config(page_title="📊 Forecast Accuracy", page_icon="🌞")
st.title("📊 Forecast Accuracy & Discrepancy Analysis")

st.markdown("""
Here we analyze how predictions made **3 or 5 days in advance** compare to the actual weather recorded on those days.
""")

# Load the data
all_data = load_forecast_data()

# Sidebar location filter
locations = sorted(set(entry["location"] for entry in all_data))
selected_location = st.sidebar.selectbox("Select a location", locations)

# Filter entries for selected location
filtered = [entry for entry in all_data if entry["location"] == selected_location]

# Pass filtered entries and selected location
threshold = render_discrepancy_checker(filtered, selected_location)

filtered_data = [entry for entry in all_data if entry.get("location") == selected_location]

st.markdown("## 🧠 Forecast Source Accuracy Rankings")
accuracy_df = evaluate_source_accuracy(filtered_data, tolerance=threshold)

if accuracy_df.empty:
    st.info("No forecast vs actual data available yet for comparison.")
else:
    st.dataframe(accuracy_df, use_container_width=True)