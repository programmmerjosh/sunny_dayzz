import os

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
    for time in ["morning", "afternoon", "evening"]:
        try:
            pred_val = int(predicted[time].strip('%'))
            actual_val = int(actual[time].strip('%'))
            if abs(pred_val - actual_val) <= tolerance:
                matches += 1
        except Exception:
            continue
    return matches

def relevant_weather_data_for(location, w_previous_weather):
    # Filter previous_weather for only this location
    # Can return "" if not relevant (or not implemented yet)
    return w_previous_weather if location.lower() in w_previous_weather.lower() else ""

def get_relevant_weather_entries(file_path, target_dates, location):
        relevant_entries = []
        location = location.lower()
        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r") as f:
            content = f.read()
            entries = content.split("_next entry_")
            for entry in entries:
                entry_clean = entry.strip().lower()
                if location in entry_clean:
                    for date in target_dates:
                        if date in entry:
                            relevant_entries.append(entry.strip())
                            break
        return "\n\n".join(relevant_entries)