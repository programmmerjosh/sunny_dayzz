def main():
    from dotenv import load_dotenv
    import os
    import datetime
    import json

    from langchain.prompts import PromptTemplate
    from langchain.llms import OpenAI
    from config import my_template_with_data, my_template_without_data

    load_dotenv()
    api_key = os.getenv("GPT_API_KEY")

    llm = OpenAI(openai_api_key=api_key, temperature=0.0, max_tokens=2048)

    today = datetime.datetime.now()
    d_todays_date = today.strftime("%d/%m/%Y")
    d_in_three_days = (today + datetime.timedelta(days=3)).strftime("%d/%m/%Y")
    d_in_seven_days = (today + datetime.timedelta(days=7)).strftime("%d/%m/%Y")
    target_dates = {d_todays_date, d_in_three_days, d_in_seven_days}

    def get_relevant_weather_entries(file_path, target_dates, location):
        relevant_entries = []
        location = location.lower()
        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r") as f:
            content = f.read()
            entries = content.split("_next entry_")
            for entry in entries:
                entry_clean = entry.strip().lower()
                if location in entry_clean:
                    for date in target_dates:
                        if date in entry:
                            relevant_entries.append(entry.strip())
                            break
        return "\n\n".join(relevant_entries)

    # 👇 Change this line to hard-code the location
    loc = "Bristol"
    str_find = "Find the predicted weather for"

    previous_data_file = "data/weather_archive.txt"
    w_previous_weather = get_relevant_weather_entries(previous_data_file, target_dates, loc)
    has_previous_data = bool(w_previous_weather.strip())
    chosen_template = my_template_with_data if has_previous_data else my_template_without_data

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

    response = llm(prompt.format(
        location=loc,
        in_seven_days=d_in_seven_days,
        in_three_days=d_in_three_days,
        todays_date=d_todays_date,
        previous_weather=w_previous_weather,
        str_find=str_find
    ))

    try:
        prediction_data = json.loads(response)
        print("✅ Successfully parsed prediction data.")
    except json.JSONDecodeError as e:
        print("❌ Failed to parse LLM response as JSON.")
        print("Raw response:")
        print(response)
        return

    json_file_path = "data/weather_data.json"
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.extend(prediction_data)

    with open(json_file_path, "w") as f:
        json.dump(existing_data, f, indent=2)

    print(f"✅ Saved {len(prediction_data)} predictions to {json_file_path}")

    # ✅ Create the logs/ folder if missing
    os.makedirs("logs", exist_ok=True) 
    with open("logs/weather_log.txt", "a") as log:
        log.write(f"[{datetime.datetime.now()}] Fetched {len(prediction_data)} predictions for {loc}\n")

if __name__ == "__main__":
    main()
