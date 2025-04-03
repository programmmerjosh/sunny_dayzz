# Sunny Dayzz is an AI weather analyst.

This small application is written in Python.
I am using LangChain (Framework) to simplfy the coding and OpenAI API to execute the AI tasks.

The purpose of this application is to automate the task of searching online for predicted weather data and actual on-the-day weather data so we can track 
how accurate the predictions are and what discrepancies we might see.
Ideally, we also want to see how often it is sunny as opposed to cloudy.

I will be refining the search criteria (prompts) so that we can start getting a more concise output. But so far, not bad.

---

### NOTE: in order for you to pull/download this project and run it yourself, you will need the following:
- an OpenAI API account, to generate an *API key* and you will need credits (which you can purchase after creating your account).
- Once you have an OpenAI API KEY, you can replace it with the *api_key* variable inside the *weather_patterns.py* file. 
- You will also need Python installed on your system. 

Then you're good to go.
Once you have all of the above set up, simply open up your terminal, navigate to the project directory and enter the following command:
`python weather.py`

### NOTE: To view the data on a visual dashboard (locally), you will need to install Streamlit.

*How to install Streamlit:*
Enter this line in your terminal: 
`pip install streamlit`

*How to run the dashboard:*
Enter this line in your terminal: 
`streamlit run dashboard.py`