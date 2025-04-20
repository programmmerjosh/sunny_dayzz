import threading
import time
import json

from datetime import datetime, timedelta, timezone
from weather_.utils import safe_get

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
    
    return safe_get(source_name="OpenMeteo", url=url)

def get_openmeteo_cloud_cover_at_time(hourly_data, date_str, time_str):
    full_target = f"{date_str}T{time_str}"
    times = hourly_data.get("hourly", {}).get("time", [])
    clouds = hourly_data.get("hourly", {}).get("cloudcover", [])
    for t, c in zip(times, clouds):
        if t == full_target:
            return {"datetime": t, "cloud_cover": c}
    return {"datetime": full_target, "cloud_cover": None, "error": "Not found"}

# 1 request per second (change this value as needed) ~ GitHub Actions is too fast for OpenMeteo's API rate allowance on their free-tier
# So, we have to slow dow calls to this API (specifically if GitHub Actions is making these API calls for us)
def rate_limited_openmeteo_call(func, *args, **kwargs):
    for attempt in range(1, 4):
        try:
            print(f"📡 Requesting from OpenMeteo (attempt {attempt})...", flush=True)
            result = func(*args, **kwargs)
            
            if result is None:
                print("❌ Received None from OpenMeteo.", flush=True)
            elif not isinstance(result, dict):
                print(f"⚠️ Unexpected result type from OpenMeteo: {type(result)}", flush=True)
            else:
                print("✅ OpenMeteo returned a response. Sample:", flush=True)
                print(json.dumps(result, indent=2)[:1000], flush=True)  # limit to avoid huge dump

            return result

        except Exception as e:
            print(f"⚠️ OpenMeteo error: {e}", flush=True)
            if attempt < 3:
                time.sleep(2)
            else:
                return None

