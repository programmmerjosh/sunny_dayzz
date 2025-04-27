import pandas as pd
# ============ 1_Cloud_Cover.py helper functions ==============
def flatten_cloud_cover(entry):
    """Extracts rows for each source from cloud cover list."""
    date = pd.to_datetime(entry["overview"]["date_for"], format="%d/%m/%Y")
    rows = []

    for source_block in entry["cloud_cover"]:
        source = source_block["source"]
        cover = source_block["data"]
        for time_utc, percent in cover.items():
            rows.append({
                "Date": date,
                "Time": time_utc,
                "Cloud Cover (%)": int(percent.strip('%')),
                "Source": source,
                "Location": entry["location"]
            })

    return rows

def average_cloud_cover_by_block(source_data):
    blocks = {
        "morning": ["06:00 UTC", "09:00 UTC"],
        "afternoon": ["12:00 UTC", "15:00 UTC"],
        "evening": ["18:00 UTC"]
    }
    block_averages = {}
    for block, times in blocks.items():
        values = [
            int(source_data[time].strip('%'))
            for time in times if time in source_data
        ]
        block_averages[block] = sum(values) / len(values) if values else None
    return block_averages

def is_sunny_day(block_averages, threshold):
    values = [v for v in block_averages.values() if v is not None]
    return (sum(values) / len(values)) <= threshold if values else False

def get_sunny_blocks(block_averages, threshold):
    return {
        block: (val is not None and val <= threshold)
        for block, val in block_averages.items()
    }

def get_combined_block_averages(entry, selected_sources):
    """
    Given an entry and list of selected sources, return a dict with the average cloud cover
    per time block (morning, afternoon, evening) across selected sources.
    """
    combined = {
        "morning": [],
        "afternoon": [],
        "evening": []
    }

    for source in entry.get("cloud_cover", []):
        if source["source"] not in selected_sources:
            continue

        block_avg = average_cloud_cover_by_block(source["data"])
        for block, value in block_avg.items():
            if value is not None:
                combined[block].append(value)

    final_avg = {
        block: (sum(values) / len(values)) if values else None
        for block, values in combined.items()
    }

    return final_avg

