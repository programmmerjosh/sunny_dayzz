import os
import json
from collections import defaultdict
import pandas as pd

DATA_FILE = os.path.join("data", "cloud_cover.json")

from collections import defaultdict
import pandas as pd

def evaluate_source_accuracy(all_data, tolerance=10):
    """
    Compare 3-day and 5-day forecast sources against 0-day actuals.
    Returns a DataFrame ranking each source by accuracy (% match within tolerance).
    """

    forecast_map = defaultdict(lambda: defaultdict(list))
    source_accuracy = defaultdict(lambda: {"total": 0, "correct": 0})

    # Step 1: Group entries by location + date
    for entry in all_data:
        try:
            location = entry["location"]
            date_for = entry["overview"]["date_for"]
            days_before = entry["overview"]["num_of_days_between_forecast"]
        except KeyError:
            continue  # Skip malformed entries

        key = f"{location}_{date_for}"
        forecast_map[key][days_before].append(entry)

    # Step 2: Compare forecasts (3-day, 5-day) to 0-day actuals
    for key, forecasts in forecast_map.items():
        if 0 not in forecasts:
            continue  # No actuals to compare against

        actual_entry = forecasts[0][0]  # Assume one actual per date/location
        actual_sources = {
            s["source"]: s["data"]
            for s in actual_entry.get("cloud_cover", [])
            if "source" in s and "data" in s
        }

        for days_before in [3, 5]:
            if days_before not in forecasts:
                continue

            prediction_entry = forecasts[days_before][0]
            for pred_source in prediction_entry.get("cloud_cover", []):
                source_name = pred_source.get("source")
                predicted = pred_source.get("data", {})

                if source_name not in actual_sources:
                    continue  # No matching actual source to compare against

                actual = actual_sources[source_name]

                for time in predicted:
                    if time in actual:
                        try:
                            pred_val = int(predicted[time].strip('%'))
                            actual_val = int(actual[time].strip('%'))

                            source_accuracy[source_name]["total"] += 1
                            if abs(pred_val - actual_val) <= tolerance:
                                source_accuracy[source_name]["correct"] += 1
                        except Exception:
                            continue

    # Step 3: Format results
    results = [
        {
            "Source": source,
            "Total Comparisons": vals["total"],
            f"Correct (≤±{tolerance}%)": vals["correct"],
            "Accuracy (%)": round((vals["correct"] / vals["total"]) * 100, 2)
            if vals["total"] > 0 else 0
        }
        for source, vals in source_accuracy.items()
    ]

    if not results:
        return pd.DataFrame()  # Empty DataFrame = no results

    return pd.DataFrame(results).sort_values("Accuracy (%)", ascending=False)

def load_forecast_data(filepath=DATA_FILE):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return []

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                print("⚠️ Unexpected format: data is not a list.")
                return []
    except json.JSONDecodeError as e:
        print(f"❌ Failed to decode JSON: {e}")
        return []