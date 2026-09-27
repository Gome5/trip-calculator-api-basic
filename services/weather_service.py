import os

import requests

from services.route_service import ExternalServiceError


WEATHER_CODES = {
    0: "Céu limpo",
    1: "Predominantemente limpo",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Névoa",
    48: "Névoa congelante",
    51: "Garoa leve",
    61: "Chuva leve",
    63: "Chuva moderada",
    65: "Chuva forte",
    71: "Neve leve",
    80: "Pancadas de chuva",
    95: "Trovoada",
}


class WeatherService:
    def __init__(self):
        self.geocoder_url = os.getenv("GEOCODER_URL", "https://nominatim.openstreetmap.org/search")
        self.weather_url = os.getenv("WEATHER_URL", "https://api.open-meteo.com/v1/forecast")
        self.timeout = float(os.getenv("EXTERNAL_API_TIMEOUT", "8"))
        self.headers = {"User-Agent": os.getenv("EXTERNAL_API_USER_AGENT", "trip-calculator-academic/1.0")}

    def get_weather(self, destination, travel_date):
        response = requests.get(
            self.geocoder_url,
            params={"q": destination, "format": "jsonv2", "limit": 1},
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        locations = response.json()
        if not locations:
            raise ExternalServiceError("Destination could not be geocoded for weather")
        forecast = requests.get(
            self.weather_url,
            params={
                "latitude": locations[0]["lat"],
                "longitude": locations[0]["lon"],
                "daily": "weather_code,temperature_2m_max",
                "timezone": "auto",
                "start_date": travel_date.isoformat(),
                "end_date": travel_date.isoformat(),
            },
            timeout=self.timeout,
        )
        forecast.raise_for_status()
        daily = forecast.json().get("daily", {})
        codes = daily.get("weather_code", [])
        temperatures = daily.get("temperature_2m_max", [])
        if not codes or not temperatures:
            raise ExternalServiceError("Weather provider returned no forecast")
        return {"weather": WEATHER_CODES.get(int(codes[0]), "Condição variável"), "temperature": float(temperatures[0])}


weather_service = WeatherService()
