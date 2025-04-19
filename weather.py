def main():
    import os
    import datetime
    import json

    from dotenv import load_dotenv
    from datetime import datetime, timezone

    from weather_.helpers import get_forecast_date, collect_cloud_cover_comparison, save_forecast_to_file
    from weather_.providers.open_weather_map import get_lat_lon

    # 🔧 Define base directory of the script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    load_dotenv(os.path.join(BASE_DIR, ".env"))
    WEATHER_API_KEY = os.getenv("FREE_TIER_OPENWEATHERMAP_API_KEY")

    log_path = os.path.join(BASE_DIR, "logs", "weather_log.txt")

    today = datetime.now(timezone.utc)
    d_in_three_days = get_forecast_date(3)
    d_in_five_days = get_forecast_date(5)
    target_dates = {today, d_in_three_days, d_in_five_days}

    # TODO: find a job for OpenAI API
    # TODO: add more weather data sources
    # TODO: test forcast accuracy new logic
    # TODO: think about ways to use the cloud cover summary ~ perhaps a table where we show a counter for each category for mornings, afternoons and nights
    # TODO: deploy the app and make sure `python weather.py` is called automatically daily

    with open("data/locations.json") as f:
        LOCATIONS = json.load(f)

    for loc in LOCATIONS:
        print(f"📍 Collecting forecast for {loc}...")
        lat, lon = get_lat_lon(loc, WEATHER_API_KEY)

        # Collect and save
        saved = 0
        generated = 0

        for forecast_date in target_dates:
            forecast_data = collect_cloud_cover_comparison(lat, lon, loc, forecast_date, WEATHER_API_KEY)
            generated += 1

            if save_forecast_to_file(forecast_data):
                saved += 1
        
        # Log
        os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
        with open(log_path, "a") as log:
            log.write(
                f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] Location: {loc}, Generated: {generated}, Saved: {saved}\n"
            )
    
if __name__ == "__main__":
    main()