from dotenv import load_dotenv 
import os
import datetime

from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

load_dotenv()

api_key = os.getenv("GPT_API_KEY")

llm = OpenAI(openai_api_key=api_key, temperature=0.0)

d_todays_date = datetime.datetime.now().strftime("%x")
date_1 = datetime.datetime.strptime(d_todays_date, "%m/%d/%y")
d_in_seven_days = date_1 + datetime.timedelta(days=7)
d_in_three_days = date_1 + datetime.timedelta(days=3)

f = open("data/weather.txt", "r")
w_previous_weather = f.read()

prompt = PromptTemplate(
    input_variables=['location', 'in_seven_days', 'in_three_days', 'todays_date', 'previous_weather'],
    template="""
    You are an AI weather data analyst.

    STEP 1. Find the predicted weather for {location} for {in_seven_days} particularly whether it is predicted to be sunny, windy, cloudy, and/or rainy and especially how much cloud cover there will be in the morning, afternoon and evening. Record the dates and times. Save the filename as {in_seven_days} plus a dash and append '7-days-before'.
    STEP 2. Find the predicted weather for {location} for {in_three_days} particularly whether it is predicted to be sunny, windy, cloudy, and/or rainy and especially how much cloud cover there will be in the morning, afternoon and evening. Record the dates and times. Save the filename as {in_three_days} plus a dash and append '3-days-before'.
    STEP 3. Find the weather for {location} for {todays_date} (morning, afternoon, and evening) particularly whether it is sunny, windy, cloudy, and/or rainy and especially how much cloud cover there is. Record the date and time. Save the filename as {todays_date} plus a dash and append 'today'.
    STEP 4. Consider the following: {previous_weather}. If, in this file, we have the recorded weather data for {todays_date}-7-days-before, {todays_date}-3-days-before, AND {todays_date}-today (which we got in STEP 3); briefly highlight ANY discrepancies, differences, changes etc so that we can understand how accurate the predictions typically are 7 days earlier and 3 days earlier.
    STEP 5. We also want to keep track of how often it is sunny in {location} and how often it is cloudy, so we can have a sunny to cloudy ratio for {location} based on our data.
    """
)

loc = input('Type the city name or geographic location for the weather data you are interested in: ')

response = llm(prompt.format(location=loc, in_seven_days=d_in_seven_days, in_three_days=d_in_three_days, todays_date=d_todays_date, previous_weather=w_previous_weather))

f = open("data/weather.txt", "a")
f.write(response)
f.close()

print(response)