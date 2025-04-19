from enum import Enum

class WeatherProvider(str, Enum):
    OPENWEATHERMAP = "OPENWEATHERMAP"
    OPENMETEO = "OPENMETEO"
