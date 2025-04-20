import os
import json
import time

from zoneinfo import ZoneInfo  # For Python 3.9+
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from enums.weather_provider import WeatherProvider

from weather_.providers.open_weather_map import fetch_owm_3hour_forecast, get_owm_3hour_cloud_cover_at_time
from weather_.providers.open_meteo import fetch_openmeteo_hourly_cloud_data, get_openmeteo_cloud_cover_at_time, rate_limited_openmeteo_call

# ========== weather.py helper functions ============
def collect_cloud_cover_comparison(lat, lon, location_name, date_for_dt, api_key):
    local_dt = get_local_datetime(datetime.now(timezone.utc), lat, lon)

    target_hours = [6, 9, 12, 15, 18]
    owm_data = {}
    om_data = {}

    def fetch_for_hour(hour):
        target_dt = date_for_dt.replace(hour=hour)

        try:
            owm_result = get_cloud_cover(lat, lon, target_dt, WeatherProvider.OPENWEATHERMAP, api_key)
        except Exception as e:
            print(f"❌ OWM error at {hour}: {e}", flush=True)
            owm_result = {"cloud_cover": None}

        try:
            om_result = get_cloud_cover(lat, lon, target_dt, WeatherProvider.OPENMETEO)
        except Exception as e:
            print(f"❌ OpenMeteo error at {hour}: {e}", flush=True)
            om_result = {"cloud_cover": None}

        time_str = f"{hour:02d}:00 UTC"
        return (time_str, owm_result.get("cloud_cover"), om_result.get("cloud_cover"))

    # 🧵 Thread pool for parallel hour-wise fetching
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_for_hour, hour) for hour in target_hours]
        for future in as_completed(futures):
            time_str, owm_cc, om_cc = future.result()
            owm_data[time_str] = format_cloud_cover(owm_cc)
            om_data[time_str] = format_cloud_cover(om_cc)

    return {
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


def get_cloud_cover(lat, lon, target_datetime_utc, provider, api_key=None):
    if provider == WeatherProvider.OPENWEATHERMAP:
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required.")
        data = fetch_owm_3hour_forecast(lat, lon, api_key)
        print("📡 Sending request to OpenWeatherMap...", flush=True)
        return get_owm_3hour_cloud_cover_at_time(data, target_datetime_utc)

    elif provider == WeatherProvider.OPENMETEO:
        days_ahead = (target_datetime_utc.date() - datetime.now(timezone.utc).date()).days

        # Round down to nearest hour
        target_hour_utc = target_datetime_utc.replace(minute=0, second=0, microsecond=0)

        data = rate_limited_openmeteo_call(fetch_openmeteo_hourly_cloud_data, lat, lon, days_ahead)
        
        if not data or "hourly" not in data:
            print("❌ OpenMeteo data is None or invalid — skipping", flush=True)
            return {
                "datetime": target_hour_utc.isoformat(),
                "cloud_cover": None,
                "error": "OpenMeteo fetch failed"
            }

        print("🌤️ Request to OpenMeteo complete", flush=True)
        date_str = target_hour_utc.strftime('%Y-%m-%d')
        time_str = target_hour_utc.strftime('%H:%M')

        return get_openmeteo_cloud_cover_at_time(data, date_str, time_str)

    else:
        raise ValueError(f"Unknown provider: {provider}")

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

    if is_duplicate(new_data, existing_data):
        print(f"🔁 Duplicate skipped: {new_data['location']} on {new_data['overview']['date_for']} ({new_data['overview']['num_of_days_between_forecast']} days before)")
        return False  # Let caller know it was skipped

    # Append new data
    existing_data.append(new_data)

    # Write back to file
    with open(filename, "w") as f:
        json.dump(existing_data, f, indent=2)

    print(f"✅ Forecast appended to {filename}")
    return True  # Let caller know it was saved

def is_duplicate(new_entry, existing_entries):
    for existing in existing_entries:
        if (
            existing["location"].lower() == new_entry["location"].lower() and
            existing["overview"]["date_for"] == new_entry["overview"]["date_for"] and
            int(existing["overview"]["num_of_days_between_forecast"]) ==
            int(new_entry["overview"]["num_of_days_between_forecast"])
        ):
            return True
    return False

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

def format_cloud_cover(raw_value):
    try:
        if raw_value is None:
            return None  # or "Missing"
        raw_str = str(raw_value).strip().lower()
        if raw_str in ["", "n/a", "na", "null"]:
            return None
        val = int(float(raw_str))
        return f"{val}%"
    except (ValueError, TypeError):
        return None
