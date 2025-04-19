
import requests

from datetime import datetime, timedelta, timezone

def fetch_openmeteo_hourly_cloud_data(lat, lon, days_ahead, timezone_str="auto"):
    now_utc = datetime.now(timezone.utc)
    target_date = (now_utc + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=cloudcover"
        f"&timezone={timezone_str}"
        f"&start_date={target_date}&end_date={target_date}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Exception thrown in fetch_openmeteo_hourly_cloud_data.\nOpen-Meteo API error: {response.status_code}")
    return response.json()

def get_openmeteo_cloud_cover_at_time(hourly_data, date_str, time_str):
    full_target = f"{date_str}T{time_str}"
    times = hourly_data.get("hourly", {}).get("time", [])
    clouds = hourly_data.get("hourly", {}).get("cloudcover", [])
    for t, c in zip(times, clouds):
        if t == full_target:
            return {"datetime": t, "cloud_cover": c}
    return {"datetime": full_target, "cloud_cover": None, "error": "Not found"}