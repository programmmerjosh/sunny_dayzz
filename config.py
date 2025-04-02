# Template WITH previous weather data
my_template_with_data = """
You are an AI weather data analyst.

We have historical weather data for context:
{previous_weather}

Generate predicted weather for {location} on the following dates:
- {in_seven_days} (7 days from now)
- {in_three_days} (3 days from now)
- {todays_date} (today)

Respond in JSON format as an array with this structure:

[
  {{
    "location": "{location}",
    "prediction_date": "DD/MM/YYYY",
    "collected_on": "{todays_date}",
    "days_before": 0 or 3 or 7,
    "summary": {{
      "morning": "...",
      "afternoon": "...",
      "evening": "..."
    }},
    "cloud_cover": {{
      "morning": "...",
      "afternoon": "...",
      "evening": "..."
    }},
    "discrepancies": "..." or "n/a"
  }}
]
"""

# Template WITHOUT previous weather data
my_template_without_data = """
You are an AI weather data analyst.

Generate predicted weather for {location} on the following dates:
- {in_seven_days} (7 days from now)
- {in_three_days} (3 days from now)
- {todays_date} (today)

You do not have access to any previous weather data.

Respond in JSON format as an array with this structure:

[
  {{
    "location": "{location}",
    "prediction_date": "DD/MM/YYYY",
    "collected_on": "{todays_date}",
    "days_before": 0 or 3 or 7,
    "summary": {{
      "morning": "...",
      "afternoon": "...",
      "evening": "..."
    }},
    "cloud_cover": {{
      "morning": "...",
      "afternoon": "...",
      "evening": "..."
    }},
    "discrepancies": "n/a"
  }}
]
"""
