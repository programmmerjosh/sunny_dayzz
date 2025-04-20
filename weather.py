import asyncio
import os
import datetime
import json

from dotenv import load_dotenv
from datetime import datetime, timezone

from weather_.helpers import get_forecast_date, collect_cloud_cover_comparison, save_forecast_to_file
from weather_.providers.open_weather_map import get_lat_lon
from weather_.metrics import get_call_counts

async def main():

    # 🔧 Define base directory of the script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    load_dotenv(os.path.join(BASE_DIR, ".env"))
    WEATHER_API_KEY = os.getenv("FREE_TIER_OPENWEATHERMAP_API_KEY")

    log_path = os.path.join(BASE_DIR, "logs", "weather_log.txt")

    today = datetime.now(timezone.utc)
    d_in_three_days = get_forecast_date(3)
    d_in_five_days = get_forecast_date(5)
    target_dates = {today, d_in_three_days, d_in_five_days}

    with open("data/locations.json") as f:
        LOCATIONS = json.load(f)

    async def process_location(loc):
        lat, lon = await get_lat_lon(loc, WEATHER_API_KEY)
        saved = 0
        generated = 0

        for forecast_date in target_dates:
            forecast_data = await collect_cloud_cover_comparison(lat, lon, loc, forecast_date, WEATHER_API_KEY)
            generated += 1

            print("📝 Writing data to file...", flush=True)
            if save_forecast_to_file(forecast_data):
                saved += 1

        print(f"✅ {loc}: {saved}/{generated} saved")

        # Log
        os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
        with open(log_path, "a") as log:
            log.write(
                f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] Location: {loc}, Generated: {generated}, Saved: {saved}\n"
            )

    await asyncio.gather(*(process_location(loc) for loc in LOCATIONS))
    counts = get_call_counts()
    print(f"📊 Total OpenMeteo API calls: {counts['OpenMeteo']}")
    print(f"📊 Total OpenWeatherMap API calls: {counts['OpenWeatherMap']}")
    
if __name__ == "__main__":
    asyncio.run(main())  # main is now async ✅
