# Template WITH previous weather data
my_template_with_data = """
You are an AI weather data analyst.

Consider the following as our collected data:
{previous_weather}

Use the format below to structure your output:
" \
"Predicted weather for [Location] on [DD/MM/yyyy] Date collected: [DD/MM/yyyy] Days before: [X]
Summary Morning: ... Afternoon: ... Evening: ...
Expected cloud cover Morning: ... Afternoon: ... Evening: ...
Discrepancies [List any if applicable]" \
"
{str_find} {location} on {in_seven_days}.
{str_find} {location} on {in_three_days}.
{str_find} {location} on {todays_date}.

Discrepancies:
Only if we have the weather data for {location} on:
- Date collected: {todays_date} (format: dd/mm/yyyy), days before: 7 and/or 3
- And Date collected: {todays_date}, days before: 0

Compare and log any discrepancies.
"""

# Template WITHOUT previous weather data
my_template_without_data = """
You are an AI weather data analyst.

{str_find} {location} on {in_seven_days}.
{str_find} {location} on {in_three_days}.
{str_find} {location} on {todays_date}.
"""
