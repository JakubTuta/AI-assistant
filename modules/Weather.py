import os
import typing

import geocoder
import requests

from helpers import decorators
from helpers.audio import Audio
from helpers.cache import Cache


class Weather:
    _api_key = os.environ.get("WEATHER_API_KEY")

    @decorators.capture_response
    @decorators.JobRegistry.register_job
    @staticmethod
    def weather(city: str) -> str:
        """
        [STANDALONE JOB] Retrieves and provides real-time weather information for any city worldwide.
        This is an independent task that fetches weather data from external APIs and provides
        complete weather reports including temperature, conditions, and location details.

        Use this job when the user wants to:
        - Get current weather conditions for any location
        - Check temperature and weather descriptions
        - Obtain weather information using geolocation if no city is specified
        - Access meteorological data for planning activities

        Keywords: weather, forecast, current weather, get weather, check weather, city weather, location weather,
                 temperature, conditions, meteorology, climate, outside weather

        Args:
            city (str): The name of the city for which to retrieve the weather.
                       If no city is specified by user the variable is set to empty string ("")
                       and the user's current geolocation is used.

        Returns:
            str: Complete weather report with city, conditions, and temperature information.
        """

        audio = Cache.get_audio()
        if audio:
            Audio.text_to_speech("Getting weather...")
        print("Getting weather...")

        if city == "":
            my_geolocation = geocoder.ip("me")

            city = my_geolocation.city
            lat, lon = my_geolocation.latlng

        else:
            lat, lon = Weather._get_coordinates_for_city_name(city)

        if lat is None or lon is None:
            return "Error: Could not retrieve coordinates for the given city."

        weather = Weather._get_weather_for_coordinates(lat, lon)

        if weather is None:
            return "Error: Could not retrieve weather information."

        string_weather = f"The weather for {city} is {weather['weather'][0]['description']} with {weather['main']['temp']}°C."

        return string_weather

    @staticmethod
    def _get_coordinates_for_city_name(
        city_name: str,
    ) -> typing.Tuple[float | None, float | None]:
        try:
            response = requests.get(
                f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={Weather._api_key}&limit=1"
            )

            data = response.json()

            if len(data) == 0:
                return None, None

            city = data[0]

            return city["lat"], city["lon"]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching coordinates: {e}")

            return None, None

    @staticmethod
    def _get_weather_for_coordinates(
        lat: float, lon: float
    ) -> typing.Dict[str, typing.Any] | None:
        try:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={Weather._api_key}&units=metric&lang=en"
            )

            data = response.json()

            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")

            return None
