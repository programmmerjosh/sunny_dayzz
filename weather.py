def main():
    import os
    import datetime
    import json

    from dotenv import load_dotenv
    from datetime import datetime, timezone
    from concurrent.futures import ThreadPoolExecutor

    from weather_.helpers import get_forecast_date, collect_cloud_cover_comparison, save_forecast_to_file
    from weather_.providers.open_weather_map import get_lat_lon

    # 🔧 Define base directory of the script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    load_dotenv(os.path.join(BASE_DIR, ".env"))
    WEATHER_API_KEY = os.getenv("FREE_TIER_OPENWEATHERMAP_API_KEY")

    log_path = os.path.join(BASE_DIR, "logs", "weather_log.txt")

    # get API keys
    gpt_key = os.getenv("GPT_API_KEY")
    owm_key = os.getenv("FREE_TIER_OPENWEATHERMAP_API_KEY")

    # print 'True' in the logs if we successfully get both API keys
    print("✅ GPT API key present:", bool(gpt_key), flush=True)
    print("✅ OpenWeather key present:", bool(owm_key), flush=True)

    today = datetime.now(timezone.utc)
    d_in_three_days = get_forecast_date(3)
    d_in_five_days = get_forecast_date(5)
    target_dates = {today, d_in_three_days, d_in_five_days}

    with open("data/locations.json") as f:
        LOCATIONS = json.load(f)

    print("🌍 Starting location loop...", flush=True)

    def process_location(loc):
        lat, lon = get_lat_lon(loc, WEATHER_API_KEY)
        saved = 0
        generated = 0

        for forecast_date in target_dates:
            forecast_data = collect_cloud_cover_comparison(lat, lon, loc, forecast_date, WEATHER_API_KEY)
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

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_location, LOCATIONS)
    
if __name__ == "__main__":
    main()