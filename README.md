# ☀️ Sunny Dayzz

Sunny Dayzz is a weather forecast accuracy app built with Streamlit, ChatGPT, and Python. It helps analyze, visualize, and validate weather prediction data collected over time — with a special focus on **cloud cover**,  **forecast accuracy**, and **sunny day identification**. 🌤️

---

## 📝 Project Overview

This project aims to track, compare, and analyze the accuracy of weather forecasts made 5 days and 3 days before the predicted date vs actual on-the-day weather predictions. We were leveraging AI to collect the weather data however, AI-collected-data proved to be inaccurate in many cases as it began to generate its own predictions based on our collected data. Now, we've moved to collecting the data from well established weather forecast APIs. The plan is to delegate other tasks to the OpenAI API in the near future. Our data collection is now automated. Over time, this data should enable users to recognize discrepancies in weather forecasts as well as weather forecast sources (and their accuracy over time) as well as keep track of daily cloud cover trends, number of sunny days (overall), mornings, afternoons, and evenings in a particular city we've collected data for and potentially so much more.

---

## 📦 Features

- 📈 **Cloud Cover Timeline**: Visualize cloud cover predictions between 6am - 6pm daily in 3 hour time-blocks
- 🔍 **Discrepancy Checker**: Compare 5/3/0 day predictions across sources for each date side-by-side
- 📊 **Forecast Accuracy Scoring**: Calculates how accurate 5-day and 3-day forecasts are versus 0-day observations
- 🥧 **Sunny vs Cloudy Ratio**: Visual breakdown of actual sunny days AND filter for sunny mornings, afternoons, or evenings
- 🗺️ **Multi-location Support**: Collect and analyze forecasts for multiple geographic locations, each with its own dashboard view
- 📅 **Automation**: Daily forecast logging is scheduled by GitHub Actions
- ☁️ **Deployed**: Hosted on Streamlit Cloud
- 🤖 **AI Ready**: OpenAI API already linked up and ready for when we have appropriate tasks to give it

---

## 🧱 Tech Stack

| Layer                 | Technology                                    |
|--------------         |---------------------------------------------- |
| UI                    | [Streamlit](https://streamlit.io)             |
| Backend Logic         | Python 3.9+ & LangChain                       |
| Data Storage          | JSON (`cloud_cover.json`)                    |
| Cloud Cover Forecasts | [OpenWeatherMap API](https://openweathermap.org/), [OpenMeteo API](https://open-meteo.com/) |
| Open AI Data Analysis (TO BE REIMPLEMENTED)  | [OpenAI GPT API](https://platform.openai.com) |
| Visuals               | Altair, Pandas                                |
| Automation            | GitHub Actions         |

---

## 🔄 JSON vs Firebase (Data Strategy)

Currently, weather data is stored in a simple local `cloud_cover.json` file. This approach is:

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
- (currently not required) An OpenAI API key with active credits  
  ➡️ [An OpenAI API key](https://platform.openai.com/account/api-keys)
- An OpenWeatherMap API key
  ➡️ [An OpenWeatherMap API key](https://openweathermap.org/api)

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
pip install streamlit
pip install requests
pip install timezonefinder
pip install python-dotenv
pip install seaborn

# Set your OpenAI API key in a .env file
echo "GPT_API_KEY=your_openai_api_key_here" > .env
echo "FREE_TIER_OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here" > .env

# Run the app locally to fetch weather predictions
python weather.py

# Launch the app
streamlit run Dashboard.py
```

## 🧪 Testing & Development Notes

- Data is stored locally in `data/cloud_cover.json`. You can inspect or modify this file directly.
- A few sample data entries are included to help you get started.
- The `weather.py` script can be run manually or automated using cron for daily forecast collection.
- The dashboard dynamically analyzes cloud cover, forecast accuracy, and sunny days in real-time based on stored JSON data.
- Feel free to update the list of locations in `data/locations.json` according to your preference.

---

## 🔒 API Key Management

- Your OpenAI API key is stored in a `.env` file and loaded via `python-dotenv`.
- Make sure to **exclude** this file from version control by adding `.env` to your `.gitignore`.
- OR
- If you're only interested in running the application locally, you could simply filter and replace `os.getenv("GPT_API_KEY")` with your own OpenAI API key

---

## 🌍 Now available 

- 🌐 [Live App](https://sunnydayzz.streamlit.app/) Hosted version on Streamlit Cloud

---

## 📌 Coming Soon

- ☁️ Firebase migration

---

## 📄 License

MIT License © [programmmerjosh]
