import requests

SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Get the current weather for a city. Returns temperature (Celsius), "
            "wind speed, and a short condition description."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Paris' or 'Chennai'",
                }
            },
            "required": ["city"],
        },
    },
}

# Open-Meteo weather codes -> readable conditions.
_WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 51: "Light drizzle", 61: "Light rain", 63: "Moderate rain",
    65: "Heavy rain", 71: "Light snow", 80: "Rain showers", 95: "Thunderstorm",
}


def execute(city: str):
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    ).json()

    results = geo.get("results")
    if not results:
        raise ValueError(f"Could not find a location matching '{city}'")

    lat, lon = results[0]["latitude"], results[0]["longitude"]

    forecast = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": True},
        timeout=10,
    ).json()

    current = forecast["current_weather"]
    return {
        "city": results[0]["name"],
        "temperature_c": current["temperature"],
        "wind_speed_kmh": current["windspeed"],
        "condition": _WEATHER_CODES.get(current["weathercode"], "Unknown"),
        "as_of": current["time"],
    }
