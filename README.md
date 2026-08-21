# ☀️ Sunny Dayzz

Sunny Dayzz visualises cloud-cover forecasts from OpenWeatherMap and Open-Meteo for nine locations.

## What the app shows

- **Same-day outlook:** when and where providers expected sunnier conditions.
- **Provider agreement:** how far the two forecasts differ.
- **Forecast drift:** how much each provider's 3- and 5-day outlook changed by the same day.

The dataset does **not** contain weather-station observations. The 0-day value is a same-day forecast reference, so the app describes forecast *drift* and *agreement*, not measured forecast accuracy.

## Run locally

Python 3.12 is used by the scheduled collector.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run Dashboard.py
```

To collect new forecasts, add an OpenWeatherMap key to `.env`:

```text
FREE_TIER_OPENWEATHERMAP_API_KEY=your_key
```

Then run:

```bash
python weather.py
```

## Daily collection

`.github/workflows/daily-weather.yml` runs at 06:00 UTC and can also be started manually. It:

1. checks out or creates `daily-data-updates`;
2. installs and verifies `requirements.txt`;
3. runs the collector with the `FREE_TIER_OPENWEATHERMAP_API_KEY` repository secret;
4. validates `data/cloud_cover.json`;
5. commits new data only when the file changed.

Collection writes the JSON atomically, uses UTC consistently, retries transient HTTP failures, and avoids duplicate records.

## Data shape

Each location/date has up to three snapshots (`0`, `3`, and `5` days before) from both providers at 06:00, 09:00, 12:00, 15:00, and 18:00 UTC. Data is stored in `data/cloud_cover.json`.
