# weather_/metrics.py
import asyncio

# Async-safe counters
openmeteo_api_calls = 0
openweathermap_api_calls = 0

# Locks for safe concurrent access
_om_lock = asyncio.Lock()
_owm_lock = asyncio.Lock()

async def increment_openmeteo_calls():
    global openmeteo_api_calls
    async with _om_lock:
        openmeteo_api_calls += 1

async def increment_openweathermap_calls():
    global openweathermap_api_calls
    async with _owm_lock:
        openweathermap_api_calls += 1

def get_call_counts():
    return {
        "OpenMeteo": openmeteo_api_calls,
        "OpenWeatherMap": openweathermap_api_calls
    }
