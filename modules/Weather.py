import typing

import geocoder
import requests

from helpers import decorators
from helpers.audio import Audio
from helpers.credentials import Credentials


class Weather:
    _api_key = Credentials.get_value("weather")

    @decorators.require_docstring
    @staticmethod
    def weather(city: str | None = None, audio: bool = False, **kwargs) -> None:
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

        print("Getting weather...")

        if city is None or city == "":
            my_geolocation = geocoder.ip("me")

            city = my_geolocation.city
            lat, lon = my_geolocation.latlng

        else:
            lat, lon = Weather.get_coordinates_for_city_name(city)

        if lat is None or lon is None:
            print("Error: Could not retrieve coordinates for the given city.")

            return

        weather = Weather.get_weather_for_coordinates(lat, lon)

        if weather is None:
            print("Error: Could not retrieve weather information.")

            return

        string_weather = f"The weather for {city} is {weather['weather'][0]['description']} with {weather['main']['temp']}°C."

        if audio:
            Audio.text_to_speech(string_weather)
        else:
            print(string_weather)

    @staticmethod
    def get_coordinates_for_city_name(
        city_name: str,
    ) -> typing.Tuple[float | None, float | None]:
        response = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={Weather._api_key}&limit=1"
        )

        data = response.json()

        if len(data) == 0:
            return None, None

        city = data[0]

        return city["lat"], city["lon"]

    @staticmethod
    def get_weather_for_coordinates(
        lat: float, lon: float
    ) -> typing.Dict[str, typing.Any] | None:
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={Weather._api_key}&units=metric&lang=en"
        )

        try:
            data = response.json()

            return data

        except:
            return None
