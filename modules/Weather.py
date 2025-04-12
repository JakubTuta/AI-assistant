import os
import typing

import geocoder
import requests

from helpers import decorators
from helpers.audio import Audio


class Weather:
    _api_key = os.environ.get("WEATHER_API_KEY")

    @decorators.capture_response
    @staticmethod
    def weather(city: str | None = None, audio: bool = False, **kwargs) -> str:
        """
        Retrieves and outputs the weather information for a given city. If no city is provided,
        it uses the user's current geolocation to determine the city.

        Args:
            city (str | None): The name of the city for which to retrieve the weather.
                                If None or empty string, the user's current geolocation is used.
            audio (bool): If True, the weather information is converted to speech. If False,
                          the weather information is printed to the console.

        Returns:
            None
        """

        if audio:
            Audio.text_to_speech("Getting weather...")
        print("Getting weather...")

        if city is None or city == "":
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
