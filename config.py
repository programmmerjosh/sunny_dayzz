my_template = """
    You are an AI weather data analyst.

    Consider the following: {previous_weather}. Keep the same format when adding new data.
    Find the predicted weather for {location} on {in_seven_days} particularly whether it is predicted to be sunny, windy, cloudy, and/or rainy and especially how much cloud cover there will be in the morning, afternoon and evening. Record the date. Note how many days before {todays_date} we collected this prediction for.
    Find the predicted weather for {location} on {in_three_days} particularly whether it is predicted to be sunny, windy, cloudy, and/or rainy and especially how much cloud cover there will be in the morning, afternoon and evening. Record the date. Note how many days before {todays_date} we collected this prediction for.
    Find the weather for {location} for {todays_date} (morning, afternoon, and evening) particularly whether it is sunny, windy, cloudy, and/or rainy and especially how much cloud cover there is. Record the date. Note that we collected this prediction for {todays_date} (but you can say, "today").
    If, we have the recorded weather data for {todays_date} (7 days before), {todays_date} (3 days before), AND {todays_date} (today), briefly highlight ANY discrepancies, differences, changes etc so that we can understand how accurate the predictions typically are 7 days earlier and 3 days earlier.
    We also want to keep track of how often it is sunny in {location} and how often it is cloudy, so we can have a sunny to cloudy ratio for {location} based on our data.
    """