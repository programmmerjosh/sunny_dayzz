import json
import os

def load_data(data_path):
    if not os.path.exists(data_path):
        return []

    with open(data_path, "r") as f:
        return json.load(f)

def get_filtered_data(data, selected_location):
    return [e for e in data if e["location"].lower() == selected_location.lower()]
            
