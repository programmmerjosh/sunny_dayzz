import requests

from datetime import datetime, timezone

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