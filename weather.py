from dotenv import load_dotenv 
import os
import datetime

from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from config import my_template

load_dotenv()

api_key = os.getenv("GPT_API_KEY")

# update max_tokens value if/when necessary to record more data
llm = OpenAI(
    openai_api_key=api_key, 
    temperature=0.0,
    max_tokens=3000, 
)

today = datetime.datetime.now()
d_todays_date = today.strftime("%d/%m/%Y")
d_in_seven_days = (today + datetime.timedelta(days=7)).strftime("%d/%m/%Y")
d_in_three_days = (today + datetime.timedelta(days=3)).strftime("%d/%m/%Y")

str_find = "Find the predicted weather for"

with open("data/weather.txt", "r") as f:
    w_previous_weather = f.read()

prompt = PromptTemplate(
    input_variables=['location', 'in_seven_days', 'in_three_days', 'todays_date', 'previous_weather', 'find'],
    template=my_template
)

loc = input('Type the city name or geographic location for the weather data you are interested in: ')

response = llm(prompt.format(location=loc, in_seven_days=d_in_seven_days, in_three_days=d_in_three_days, todays_date=d_todays_date, previous_weather=w_previous_weather, find=str_find))

with open("data/weather.txt", "a") as f:
    f.write("\n" + response + "\n")
    f.close()

print(response)