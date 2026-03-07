collect_cloud_cover_template = """
You are an AI weather data collector.

Fetch real historical weather data for {location} from two of these sources: 
1. NOAA National Centers for Environmental Information (NCEI)
2. ECMWF / ERA5 (Copernicus Climate Data Store)
3. Meteostat

We are specifically interested in cloud cover for EVERY day within our date range at these particular hours: 06:00, 09:00, 12:00, 15:00, and 18:00.

Our date range is from {start_date} to {end_date}.

Result Format:
[
  {{
    "location": "city name",
    "overview": {{
      "date_for": "dd/mm/yyyy",
      "date_time_collected": "{todays_date}",
      "historical": true
    }},
    "cloud_cover": [
      {{
        "source": "source name",
        "data": {{
          "06:00 UTC": "%",
          "09:00 UTC": "%",
          "12:00 UTC": "%",
          "15:00 UTC": "%",
          "18:00 UTC": "%"
        }}
      }},
      {{
        "source": "source name",
        "data": {{
          "06:00 UTC": "%",
          "09:00 UTC": "%",
          "12:00 UTC": "%",
          "15:00 UTC": "%",
          "18:00 UTC": "%"
        }}
      }}
    ]
  }}
]
"""