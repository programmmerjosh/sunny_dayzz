import os
import json
import tempfile

from zoneinfo import ZoneInfo  # For Python 3.9+
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta, timezone

from enums.weather_provider import WeatherProvider

from weather_.providers.open_weather_map import fetch_owm_3hour_forecast, get_owm_3hour_cloud_cover_at_time
from weather_.providers.open_meteo import fetch_openmeteo_hourly_cloud_data, get_openmeteo_cloud_cover_at_time, rate_limited_openmeteo_call

# ========== weather.py helper functions ============
async def collect_cloud_cover_comparison(
    lat, lon, location_name, date_for_dt, api_key, owm_shared=None
):
    # 🌍 Local datetime (for logging/metadata)
    local_dt = get_local_datetime(datetime.now(timezone.utc), lat, lon)

    # 🕒 Target forecast hours
    target_hours = [6, 9, 12, 15, 18]

    # 📦 Prepare containers
    owm_data = {}
    om_data = {}

    # 📆 Days ahead for OpenMeteo request
    days_ahead = (date_for_dt.date() - datetime.now(timezone.utc).date()).days

    # 🚀 Prefetch both APIs just once
    try:
        if owm_shared is None:
            owm_shared = await fetch_owm_3hour_forecast(lat, lon, api_key)
            print("📡 OpenWeatherMap forecast fetched", flush=True)
    except Exception as e:
        print(f"❌ Failed to fetch OpenWeatherMap: {e}", flush=True)
        owm_shared = None

    try:
        om_shared = await rate_limited_openmeteo_call(fetch_openmeteo_hourly_cloud_data, lat, lon, days_ahead)
        print("🌤️ OpenMeteo forecast fetched", flush=True)
    except Exception as e:
        print(f"❌ Failed to fetch OpenMeteo: {e}", flush=True)
        om_shared = None

    # 🔁 Loop through each forecast hour
    for hour in target_hours:
        target_dt = date_for_dt.replace(hour=hour)

        if owm_shared:
            try:
                owm_result = await get_cloud_cover(lat, lon, target_dt, WeatherProvider.OPENWEATHERMAP, api_key, shared_data=owm_shared)
            except Exception as e:
                print(f"❌ OWM error at {hour}: {e}", flush=True)
                owm_result = {"cloud_cover": None}
        else:
            owm_result = {"cloud_cover": None}

        if om_shared:
            try:
                om_result = await get_cloud_cover(lat, lon, target_dt, WeatherProvider.OPENMETEO, shared_data=om_shared)
            except Exception as e:
                print(f"❌ OpenMeteo error at {hour}: {e}", flush=True)
                om_result = {"cloud_cover": None}
        else:
            om_result = {"cloud_cover": None}

        time_str = f"{hour:02d}:00 UTC"
        owm_data[time_str] = format_cloud_cover(owm_result.get("cloud_cover"))
        om_data[time_str] = format_cloud_cover(om_result.get("cloud_cover"))

    # 📦 Build the output structure
    return {
        "location": location_name,
        "overview": {
            "date_for": date_for_dt.strftime("%d/%m/%Y"),
            "date_time_collected": local_dt.strftime("%d/%m/%Y %H:%M"),
            "num_of_days_between_forecast": days_ahead
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

async def get_cloud_cover(lat, lon, target_datetime_utc, provider, api_key=None, shared_data=None):
    if provider == WeatherProvider.OPENWEATHERMAP:
        if not api_key:
            raise ValueError("OpenWeatherMap API key is required.")
        data = shared_data or await fetch_owm_3hour_forecast(lat, lon, api_key)
        print("📡 Sending request to OpenWeatherMap...", flush=True)
        return get_owm_3hour_cloud_cover_at_time(data, target_datetime_utc)

    elif provider == WeatherProvider.OPENMETEO:
        days_ahead = (target_datetime_utc.date() - datetime.now(timezone.utc).date()).days
        target_hour_utc = target_datetime_utc.replace(minute=0, second=0, microsecond=0)

        data = shared_data or await rate_limited_openmeteo_call(fetch_openmeteo_hourly_cloud_data, lat, lon, days_ahead)

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

    # Write atomically so a cancelled run cannot leave invalid JSON behind.
    output_dir = os.path.dirname(filename) or "."
    os.makedirs(output_dir, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=output_dir, delete=False, encoding="utf-8"
        ) as temp_file:
            temp_path = temp_file.name
            json.dump(existing_data, temp_file, indent=2, ensure_ascii=False)
            temp_file.write("\n")
        os.replace(temp_path, filename)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

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
        try:
            return int(str(value).strip().rstrip('%')) if value is not None else None
        except (TypeError, ValueError):
            return None

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
    morning_vals = [percent_str_to_int(cloud_data.get("06:00 UTC")),
                    percent_str_to_int(cloud_data.get("09:00 UTC"))]
    afternoon_vals = [percent_str_to_int(cloud_data.get("12:00 UTC")),
                      percent_str_to_int(cloud_data.get("15:00 UTC"))]
    evening_vals = [percent_str_to_int(cloud_data.get("18:00 UTC"))]

    # Compute averages
    def average(values):
        available = [value for value in values if value is not None]
        return sum(available) // len(available) if available else None

    # Interpret summary
    return {
        "morning": interpret_cloud_cover(average(morning_vals)) if average(morning_vals) is not None else "Unavailable",
        "afternoon": interpret_cloud_cover(average(afternoon_vals)) if average(afternoon_vals) is not None else "Unavailable",
        "evening": interpret_cloud_cover(average(evening_vals)) if average(evening_vals) is not None else "Unavailable"
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
