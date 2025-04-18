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
    
def build_discrepancy_map(entries):
    """
    Group forecast entries by location → date_for → source → list of forecasts.
    Each list contains different forecast ages (e.g. 7-day, 3-day, 0-day).
    """
    prediction_map = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for entry in entries:
        location = entry.get("location")
        overview = entry.get("overview", {})
        date_for = overview.get("date_for")
        source_blocks = entry.get("cloud_cover", [])

        for block in source_blocks:
            source = block.get("source")
            if not all([location, date_for, source]):
                continue  # skip invalid entries

            prediction_map[location][date_for][source].append({
                "days_before": overview.get("num_of_days_between_forecast"),
                "collected_on": overview.get("date_time_collected"),
                "data": block.get("data", {}),
                "summary": block.get("summary", {})
            })

    return prediction_map

def get_discrepancies_for_date(source_data_by_day, threshold, filter_days=None):
    """
    Returns:
        - list of dicts with: hour, source, days_before, value
        - set of (hour, source, days_before) to highlight (if discrepancy > threshold)
    """
    from collections import defaultdict

    all_rows = []
    highlight_cells = set()
    hour_values_by_time = defaultdict(list)  # hour → list of (value, source, day_label)

    for source, forecasts in source_data_by_day.items():
        for forecast in forecasts:
            days_before = forecast.get("days_before")
            days_label = f"{days_before}d"

            if filter_days and days_label not in filter_days:
                continue  # ✅ skip if forecast age is not selected

            data = forecast.get("data", {})

            for hour, val in data.items():
                try:
                    value = int(str(val).strip('%'))
                except (ValueError, TypeError):
                    value = None

                all_rows.append({
                    "Hour": hour,
                    "Source": source,
                    "Days Before": days_label,
                    "Cloud Cover (%)": value
                })

                if value is not None:
                    hour_values_by_time[hour].append((value, source, days_label))

    # ✅ Now detect discrepancies
    for hour, values in hour_values_by_time.items():
        if len(values) < 2:
            continue

        raw_values = [v[0] for v in values]
        if max(raw_values) - min(raw_values) > threshold:
            for (_, src, day) in values:
                highlight_cells.add((hour, src, day))

    return all_rows, highlight_cells

