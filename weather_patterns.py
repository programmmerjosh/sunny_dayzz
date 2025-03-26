from dotenv import load_dotenv 
import os
import datetime

from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from config import my_template

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
    template=my_template
)

loc = input('Type the city name or geographic location for the weather data you are interested in: ')

response = llm(prompt.format(location=loc, in_seven_days=d_in_seven_days, in_three_days=d_in_three_days, todays_date=d_todays_date, previous_weather=w_previous_weather))

f = open("data/weather.txt", "a")
f.write(response)
f.close()

print(response)