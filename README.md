# ☀️ Sunny Dayzz

Sunny Dayzz is an AI-powered weather app built with Streamlit, OpenAI, and Python. It helps analyze, visualize, and validate weather prediction data collected over time — with a special focus on **forecast accuracy** and **sunny day identification**. 🌤️

---

## 📝 Project Overview

This project aims to track, compare, and analyze the accuracy of weather forecasts made 7 days and 3 days before the predicted date vs actual on-the-day weather predictions. *We are leveraging AI and automation to handle the tasks of initiating the collection of the data AND producing a visual analysis of our results.* Over time, this data enables users to monitor model drift, forecast consistency, and real-world accuracy — with automated analysis of discrepancies and daily cloud cover trends.

---

## 📦 Features

- 📈 **Cloud Cover Timeline**: Visualize cloud cover predictions across all time blocks (morning, afternoon, evening)
- 🔍 **Discrepancy Checker**: Compare 7/3/0 day predictions for each date side-by-side
- ☀️ **Sunny Day Detection**: Automatically flags days with clear weather
- 📊 **Forecast Accuracy Scoring**: Calculates how accurate 7-day and 3-day forecasts are versus 0-day observations
- 🥧 **Sunny vs Cloudy Ratio**: Visual breakdown of actual sunny days
- 📅 **Automation Ready**: Daily forecast logging is scheduled locally using cron
- ☁️ **Deployment-Ready**: Next step: hosting via Streamlit Cloud or other providers

---

## 🧱 Tech Stack

| Layer        | Technology                                  |
|--------------|----------------------------------------------|
| UI           | [Streamlit](https://streamlit.io)           |
| Backend Logic| Python 3.9+ & LangChain                                 |
| Data Storage | JSON (`weather_data.json`)                  |
| AI Forecasts | [OpenAI GPT API](https://platform.openai.com) |
| Visuals      | Altair, Pandas                              |
| Automation   | Local cron job for daily predictions        |

---

## 🔄 JSON vs Firebase (Data Strategy)

Currently, weather data is stored in a simple local `weather_data.json` file. This approach is:

✅ Perfect for early-stage projects  
✅ Fast, free, and easy to version  
✅ Sufficient for small datasets (~1–5MB)

Later, the project may migrate to **Firebase Realtime Database** if:
- Data size grows significantly
- Real-time access or multi-user editing is needed
- A mobile app or remote clients are added

For now, JSON is the ideal lightweight storage choice. No need to complicate the architecture prematurely.

---

## ⚙️ Getting Started

To run this project locally, you'll need:

### ✅ Requirements
- Python 3.9+
- An OpenAI API key with active credits  
  ➡️ [Get an API key here](https://platform.openai.com/account/api-keys)

### 📦 Recommended Install Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/sunny-dayzz.git
cd sunny-dayzz

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key in a .env file
echo "GPT_API_KEY=your_openai_api_key_here" > .env

# Run the app locally to generate predictions
python weather.py

# Launch the interactive dashboard
streamlit run dashboard.py

## 🧪 Testing & Development Notes

- Data is stored locally in `data/weather_data.json`. You can inspect or modify this file directly.
- A few sample data entries are included to help you get started.
- The `weather.py` script can be run manually or automated using cron for daily forecast collection.
- The dashboard dynamically analyzes cloud cover, forecast accuracy, and sunny days in real-time based on stored JSON data.

---

## 🔒 API Key Management

- Your OpenAI API key is stored in a `.env` file and loaded via `python-dotenv`.
- Make sure to **exclude** this file from version control by adding `.env` to your `.gitignore`.
OR
- If you're only interested in running the application locally, you could simply filter and replace `os.getenv("GPT_API_KEY")` with your own OpenAI API key

---

## 📌 Coming Soon

- 🌐 Hosted version on Streamlit Cloud
- ☁️ Firebase migration (optional)

---

## 📄 License

MIT License © [programmmerjosh]