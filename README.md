# ☀️ Sunny Dayzz

Sunny Dayzz visualises cloud-cover forecasts from OpenWeatherMap and Open-Meteo for nine locations.

## What the app shows

- **Seasonal dashboard:** typical clear-sky and cloud-cover outlooks calculated from all available same-day forecasts. Spring, Summer, Autumn, and Winter are matched to each location's hemisphere, so Port Elizabeth uses Southern Hemisphere seasons.
- **Latest available outlook:** a clearly dated, secondary view of the most recent same-day forecast in the merged dataset.
- **Data freshness and sample size:** the dashboard states how current the merged data is and how many forecast dates support each seasonal comparison.
- **Same-day history:** when and where providers expected sunnier conditions.
- **Provider agreement:** how far the two forecasts differ.
- **Forecast drift:** how much each provider's 3- and 5-day outlook changed by the same day.

For the seasonal dashboard, provider and daytime readings are averaged into one value per location and date first. Those daily values are then averaged for the selected local season, ensuring that every date contributes equally. Clear sky is calculated as `100% - cloud cover`.

### Cloud Cover page

The Cloud Cover page explores same-day forecasts for one location over a selected 30-day, 90-day, or complete history window. Users can choose the providers and set the maximum cloud-cover percentage that counts as a mostly clear day.

- **Clear sky by time of day:** a grey-to-gold grid groups forecasts into Morning (06:00 and 09:00 UTC), Afternoon (12:00 and 15:00 UTC), and Evening (18:00 UTC). More gold consistently means more expected clear sky, while a gold outline identifies periods that meet the selected sunny-day limit.
- **Plain-language summary:** shows the share of mostly clear days, typical clear sky, clearest time of day, and typical difference between providers.
- **Provider outlooks:** places the daily provider history beside the latest available day's provider comparison.
- **Time-of-day frequency:** shows both the count and percentage of selected dates when each period was mostly clear, making the active history window explicit.

Displayed clear-sky and cloud-cover values are rounded as complementary pairs so they always total exactly 100%.

The dataset does **not** contain weather-station observations. The 0-day value is a same-day forecast reference, so the app describes forecast patterns, drift, and provider agreement—not measured weather or forecast accuracy.

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

Collected records are stored on the `daily-data-updates` branch. Until that branch is merged, the deployed dashboard may not include the newest collection. The dashboard therefore displays both the latest available data date and how many days it is behind the current date.

## Data shape

Each location/date has up to three snapshots (`0`, `3`, and `5` days before) from both providers at 06:00, 09:00, 12:00, 15:00, and 18:00 UTC. Data is stored in `data/cloud_cover.json`.

Meteorological seasons are grouped as follows:

| Northern Hemisphere | Months | Southern Hemisphere |
| --- | --- | --- |
| Winter | December–February | Summer |
| Spring | March–May | Autumn |
| Summer | June–August | Winter |
| Autumn | September–November | Spring |
