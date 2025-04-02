from dotenv import load_dotenv
import os
import datetime

from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from config import my_template_with_data, my_template_without_data

load_dotenv()
api_key = os.getenv("GPT_API_KEY")

# Initialize OpenAI LLM with higher token allowance
llm = OpenAI(openai_api_key=api_key, temperature=0.0, max_tokens=2048)

# Format today's and future dates
today = datetime.datetime.now()
d_todays_date = today.strftime("%d/%m/%Y")
d_in_three_days = (today + datetime.timedelta(days=3)).strftime("%d/%m/%Y")
d_in_seven_days = (today + datetime.timedelta(days=7)).strftime("%d/%m/%Y")

# Collect all dates we want to predict for
target_dates = {d_todays_date, d_in_three_days, d_in_seven_days}


def get_relevant_weather_entries(file_path, target_dates, location):
    """Filter weather history for matching location and date."""
    relevant_entries = []
    location = location.lower()

    with open(file_path, "r") as f:
        content = f.read()
        entries = content.split("_next entry_")
        for entry in entries:
            entry_clean = entry.strip().lower()
            if location in entry_clean:
                for date in target_dates:
                    if date in entry:
                        relevant_entries.append(entry.strip())
                        break  # stop checking dates once one matches
    return "\n\n".join(relevant_entries)


# Ask user for the location
loc = input('Type the city name or geographic location for the weather data you are interested in: ')
str_find = "Find the predicted weather for"

# Load relevant previous weather (filtered)
w_previous_weather = get_relevant_weather_entries("data/weather.txt", target_dates, loc)
has_previous_data = bool(w_previous_weather.strip())

# Choose the appropriate prompt template
chosen_template = my_template_with_data if has_previous_data else my_template_without_data

# Build the prompt
prompt = PromptTemplate(
    input_variables=[
        'location',
        'in_seven_days',
        'in_three_days',
        'todays_date',
        'previous_weather',
        'str_find'
    ],
    template=chosen_template
)

# Generate the LLM response
response = llm(prompt.format(
    location=loc,
    in_seven_days=d_in_seven_days,
    in_three_days=d_in_three_days,
    todays_date=d_todays_date,
    previous_weather=w_previous_weather,
    str_find=str_find
))

# Save new prediction to file
with open("data/weather.txt", "a") as f:
    f.write("\n" + response.strip() + "\n_next entry_\n")

# Output result
print(response)
