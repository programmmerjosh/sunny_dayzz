import streamlit as st

from forecast_analysis_.helpers import evaluate_source_accuracy, load_forecast_data

st.set_page_config(page_title="📊 Forecast Accuracy", page_icon="📊")
st.title("📊 Forecast Accuracy & Discrepancy Analysis")

st.markdown("""
Here we analyze how predictions made **3 or 5 days in advance** compare to the actual weather recorded on those days.
""")

st.markdown("## 🧠 Forecast Source Accuracy Rankings")

# Load the data
all_data = load_forecast_data()
accuracy_df = evaluate_source_accuracy(all_data)

if accuracy_df.empty:
    st.info("No forecast vs actual data available yet for comparison.")
else:
    st.dataframe(accuracy_df, use_container_width=True)

