import streamlit as st
from collections import defaultdict
from .helpers import is_sunny, compare_cloud_cover

def render_discrepancy_checker(filtered):
    st.markdown("## 🔍 Prediction Discrepancy Checker")
    prediction_map = defaultdict(dict)
    for entry in filtered:
        prediction_map[entry["prediction_date"]][int(entry["days_before"])] = entry

    for pred_date, predictions in prediction_map.items():
        if all(x in predictions for x in [0, 3, 7]):
            with st.expander(f"📅 {pred_date} - Compare 7/3/0 Day Forecasts"):
                cols = st.columns(3)
                for i, day in enumerate([7, 3, 0]):
                    e = predictions[day]
                    with cols[i]:
                        st.markdown(f"**{day} Days Before** {'☀️' if is_sunny(e['cloud_cover']) else ''}")
                        st.write("Summary", e["summary"])
                        st.write("Cloud Cover", e["cloud_cover"])
                        if e.get("discrepancies") and e["discrepancies"].lower() != "n/a":
                            st.warning(e["discrepancies"])

    return prediction_map

def render_forecast_accuracy(prediction_map):
    seven_day_scores = []
    three_day_scores = []
    total_possible = 0

    for pred_date, predictions in prediction_map.items():
        if all(day in predictions for day in [0, 3, 7]):
            actual = predictions[0]["cloud_cover"]
            score7 = compare_cloud_cover(predictions[7]["cloud_cover"], actual)
            score3 = compare_cloud_cover(predictions[3]["cloud_cover"], actual)
            seven_day_scores.append(score7)
            three_day_scores.append(score3)
            total_possible += 3

    accuracy_7 = round((sum(seven_day_scores) / total_possible) * 100, 2) if total_possible > 0 else 0
    accuracy_3 = round((sum(three_day_scores) / total_possible) * 100, 2) if total_possible > 0 else 0

    st.markdown("## 📊 Forecast Accuracy (vs 0-Day Actuals)")
    st.metric("7-Day Forecast Accuracy", f"{accuracy_7}%")
    st.metric("3-Day Forecast Accuracy", f"{accuracy_3}%")
