my_template = """
    You are an AI weather data analyst.

    Consider the following as our collected data: {previous_weather}.

    Consider the following example to maintain a consistent format:
    ```
   *Predicted weather for Bristol on DD/MM/yyyy*
    Date collected: DD/MM/yyyy
    Days before: 7
    ---
    *Summary*
    Morning: Partly cloudy
    Afternoon: Mostly sunny
    Evening: Partly cloudy
    ---
    *Expected cloud cover*
    Morning: 30%
    Afternoon: 10%
    Evening: 20%
    ---
    *Discrepancies*
    n/a
    ```

    {find} {location} on {in_seven_days}.
    {find} {location} on {in_three_days}.
    {find} {location} on {todays_date}.
    
    Discrepancies:
    Only if we have the weather data for {location} on 
    Date collected: {todays_date} (format: dd/mm/yyyy), 
    days before: 7 and/or 3 as well as 
    Date collected: {todays_date} (format: dd/mm/yyyy), 
    days before: 0; 
    log any discrepancies.
    """