import json
import os
from collections import defaultdict

import pandas as pd

from cloud_cover_.helpers import _parse_percent


DATA_FILE = os.path.join("data", "cloud_cover.json")


def load_forecast_data(filepath=DATA_FILE):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def build_comparison_dataframe(entries):
    """Compare 3/5-day outlooks with the matching provider's same-day outlook."""
    grouped = defaultdict(dict)
    for entry in entries:
        overview = entry.get("overview", {})
        key = (entry.get("location"), overview.get("date_for"))
        lead = overview.get("num_of_days_between_forecast")
        if not key[0] or not key[1] or lead not in (0, 3, 5):
            continue
        grouped[key][int(lead)] = entry

    rows = []
    for (location, date_for), forecasts in grouped.items():
        if 0 not in forecasts:
            continue
        reference = {
            block.get("source"): block.get("data", {})
            for block in forecasts[0].get("cloud_cover", [])
        }
        for lead in (3, 5):
            if lead not in forecasts:
                continue
            for block in forecasts[lead].get("cloud_cover", []):
                source = block.get("source")
                if source not in reference:
                    continue
                for hour, raw_forecast in block.get("data", {}).items():
                    forecast = _parse_percent(raw_forecast)
                    same_day = _parse_percent(reference[source].get(hour))
                    if forecast is None or same_day is None:
                        continue
                    rows.append(
                        {
                            "Location": location,
                            "Date": pd.to_datetime(date_for, format="%d/%m/%Y"),
                            "Hour": hour,
                            "Source": source.replace(".com", ""),
                            "Lead time": f"{lead} days",
                            "Days before": lead,
                            "Forecast cloud (%)": forecast,
                            "Same-day cloud (%)": same_day,
                            "Difference (pp)": forecast - same_day,
                            "Absolute difference (pp)": abs(forecast - same_day),
                        }
                    )
    return pd.DataFrame(rows)


def evaluate_source_accuracy(all_data, tolerance=10):
    """Compatibility helper returning agreement with same-day outlooks."""
    comparisons = build_comparison_dataframe(all_data)
    if comparisons.empty:
        return pd.DataFrame()
    comparisons["Within tolerance"] = comparisons["Absolute difference (pp)"] <= tolerance
    summary = (
        comparisons.groupby(["Source", "Lead time"], as_index=False)
        .agg(
            Comparisons=("Within tolerance", "size"),
            **{
                "Mean difference (pp)": ("Absolute difference (pp)", "mean"),
                "Agreement (%)": ("Within tolerance", "mean"),
            },
        )
    )
    summary["Mean difference (pp)"] = summary["Mean difference (pp)"].round(1)
    summary["Agreement (%)"] = (summary["Agreement (%)"] * 100).round(1)
    return summary.sort_values(["Mean difference (pp)", "Source"])


def build_discrepancy_map(entries):
    prediction_map = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for entry in entries:
        location = entry.get("location")
        overview = entry.get("overview", {})
        date_for = overview.get("date_for")
        for block in entry.get("cloud_cover", []):
            source = block.get("source")
            if not all([location, date_for, source]):
                continue
            prediction_map[location][date_for][source].append(
                {
                    "days_before": overview.get("num_of_days_between_forecast"),
                    "collected_on": overview.get("date_time_collected"),
                    "data": block.get("data", {}),
                    "summary": block.get("summary", {}),
                }
            )
    return prediction_map


def get_discrepancies_for_date(source_data_by_day, threshold, filter_days=None):
    all_rows = []
    by_hour = defaultdict(list)
    for source, forecasts in source_data_by_day.items():
        for forecast in forecasts:
            days_label = f"{forecast.get('days_before')}d"
            if filter_days and days_label not in filter_days:
                continue
            for hour, raw_value in forecast.get("data", {}).items():
                value = _parse_percent(raw_value)
                all_rows.append({"Hour": hour, "Source": source, "Days Before": days_label, "Cloud Cover (%)": value})
                if value is not None:
                    by_hour[hour].append((value, source, days_label))
    highlights = {
        (hour, source, day)
        for hour, values in by_hour.items()
        if len(values) > 1 and max(value for value, _, _ in values) - min(value for value, _, _ in values) > threshold
        for _, source, day in values
    }
    return all_rows, highlights
