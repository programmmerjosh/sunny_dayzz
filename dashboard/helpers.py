import os
import requests
import json

from enums.weather_provider import WeatherProvider
from datetime import datetime, timedelta, timezone
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo  # For Python 3.9+

# ========== top layer ============
def collect_cloud_cover_comparison(lat, lon, location_name, date_for_dt, api_key):

    # today's date and current (local) time
    local_dt = get_local_datetime(datetime.now(timezone.utc), lat, lon) # NOTE: for this variable, that we are storing in our json data as: date_time_collected, will be the local date (and time) of the location we are looking for. NOT necessarily the time we see wherever we are running the application from.

    # Define forecast times
    target_hours = [6, 9, 12, 15, 18]

    # Prepare the containers
    owm_data = {}
    om_data = {}

    for hour in target_hours:
        target_dt = date_for_dt.replace(hour=hour)

        owm_result = get_cloud_cover(lat, lon, target_dt, WeatherProvider.OPENWEATHERMAP, api_key)
        om_result = get_cloud_cover(lat, lon, target_dt, WeatherProvider.OPENMETEO)

        time_str = f"{hour:02d}:00 UTC"
        owm_data[time_str] = f"{owm_result['cloud_cover']}%" if owm_result['cloud_cover'] is not None else "N/A"
        om_data[time_str] = f"{om_result['cloud_cover']}%" if om_result['cloud_cover'] is not None else "N/A"

    # Build the JSON structure
    output = {
        "location": location_name,
        "overview": {
            "date_for": date_for_dt.strftime("%d/%m/%Y"),
            "date_time_collected": local_dt.strftime("%d/%m/%Y %H:%M"), 
            "num_of_days_between_forecast": (date_for_dt.date() - datetime.now(timezone.utc).date()).days
        },
        "cloud_cover": [
            {
                "source": "OpenWeatherMap.com",
                "data": owm_data,
                "summary": generate_cloud_summary(owm_data)
            },
            {
                "source": "OpenMeteo.com",
                "data": om_data,
                "summary": generate_cloud_summary(om_data)
            }
        ],
    }

    return output

def get_cloud_cover(lat, lon, target_datetime_utc, provider, api_key=None):
    if provider == WeatherProvider.OPENWEATHERMAP:
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required.")
        data = fetch_owm_3hour_forecast(lat, lon, api_key)
        return get_owm_3hour_cloud_cover_at_time(data, target_datetime_utc)

    elif provider == WeatherProvider.OPENMETEO:
        days_ahead = (target_datetime_utc.date() - datetime.now(timezone.utc).date()).days
        data = fetch_openmeteo_hourly_cloud_data(lat, lon, days_ahead)
        date_str = target_datetime_utc.strftime('%Y-%m-%d')
        time_str = target_datetime_utc.strftime('%H:%M')
        return get_openmeteo_cloud_cover_at_time(data, date_str, time_str)

    else:
        raise ValueError(f"Unknown provider: {provider}")

# ======================

# ============ platform specific functions ==============
# ====== Open Weather Map =======
def get_lat_lon(city_name, api_key):

    if not api_key:
        raise Exception("API key not found. Did you set it in the .env file?")
    
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if not data:
        raise Exception(f"City '{city_name}' not found.")
    
    lat = data[0]['lat']
    lon = data[0]['lon']
    return lat, lon
    
def fetch_owm_3hour_forecast(lat, lon, api_key):
    """
    LIMITATIONS OF FREE TIER OPENWEATHERMAP API:
    Hourly forecast: unavailable
    Daily forecast: unavailable
    Calls per minute: 60
    3 hour forecast: (upt to) 5 days
    """
    url = (
        f"http://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&units=metric&appid={api_key}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Exception thrown in fetch_owm_3hour_forecast.\nOpenWeatherMap API error: {response.status_code} - {response.text}")
    
    return response.json()

def get_owm_3hour_cloud_cover_at_time(data, target_dt_utc):
    closest_entry = None
    min_diff = float('inf')

    for entry in data.get("list", []):
        forecast_time = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        diff = abs((forecast_time - target_dt_utc).total_seconds())

        if diff < min_diff:
            min_diff = diff
            closest_entry = entry

    if closest_entry:
        return {
            "datetime": datetime.fromtimestamp(closest_entry["dt"], tz=timezone.utc).isoformat(),
            "cloud_cover": closest_entry["clouds"]["all"]
        }

    return {
        "datetime": target_dt_utc.isoformat(),
        "cloud_cover": None,
        "error": "No matching data found"
    }

# ===========

# ====== Open Meteo =======
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

# ===========
# ======================

# ============ supporting functions ==============
def save_forecast_to_file(new_data, filename="data/cloud_cover.json"):
    # Load existing data if file exists
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    # Append new data
    existing_data.append(new_data)

    # Write back to file
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=2)

    print(f"✅ Forecast appended to {filename}")

def get_forecast_date(days_from_today: int = 0):
    """
    Returns a timezone-aware datetime (UTC) at midnight for a future date.
    Example: get_forecast_date(7) → 7 days from today at 00:00 UTC
    """
    now_utc = datetime.now(timezone.utc)
    forecast_date = now_utc + timedelta(days=days_from_today)
    return forecast_date.replace(hour=0, minute=0, second=0, microsecond=0)

def get_local_datetime(utc_datetime, lat, lon):
    """
    Converts a UTC datetime to the local timezone of the given coordinates.
    Falls back to UTC if timezone lookup fails.
    """
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        if tz_name:
            return utc_datetime.astimezone(ZoneInfo(tz_name))
        else:
            print("⚠️ Timezone not found for coordinates. Falling back to UTC.")
    except Exception as e:
        print(f"⚠️ Timezone lookup failed: {e}. Falling back to UTC.")
    
    return utc_datetime.astimezone(timezone.utc)

def generate_cloud_summary(cloud_data):
    """
    Generates a weather summary for morning, afternoon, and evening based on cloud cover data.
    Expects values in the format: {"06:00 UTC": "5%", "09:00 UTC": "10%", ...}
    """
    def percent_str_to_int(value):
        return int(value.strip('%')) if value and value.endswith('%') else 0

    def interpret_cloud_cover(average):
        if 0 <= average <= 10:
            return "Sunny & Clear"
        elif 11 <= average <= 30:
            return "Mostly sunny. Partly cloudy"
        elif 31 <= average <= 40:
            return "Partly cloudy"
        elif 41 <= average <= 60:
            return "Cloudy"
        elif 61 <= average <= 85:
            return "Mostly Overcast"
        elif 86 <= average <= 100:
            return "Fully Overcast"
        return "Unknown"

    # Extract and convert values
    morning_vals = [percent_str_to_int(cloud_data.get("06:00 UTC", "0%")),
                    percent_str_to_int(cloud_data.get("09:00 UTC", "0%"))]
    afternoon_vals = [percent_str_to_int(cloud_data.get("12:00 UTC", "0%")),
                      percent_str_to_int(cloud_data.get("15:00 UTC", "0%"))]
    evening_val = percent_str_to_int(cloud_data.get("18:00 UTC", "0%"))

    # Compute averages
    morning_avg = sum(morning_vals) // len(morning_vals)
    afternoon_avg = sum(afternoon_vals) // len(afternoon_vals)

    # Interpret summary
    return {
        "morning": interpret_cloud_cover(morning_avg),
        "afternoon": interpret_cloud_cover(afternoon_avg),
        "evening": interpret_cloud_cover(evening_val)
    }
# ======================












# ============ older functions that require updating ==============
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

def is_duplicate(new_entry, existing_entries):
    for existing in existing_entries:
        if (
            existing["location"].lower() == new_entry["location"].lower() and
            existing["prediction_date"] == new_entry["prediction_date"] and
            int(existing["days_before"]) == int(new_entry["days_before"])
        ):
            return True
    return False

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