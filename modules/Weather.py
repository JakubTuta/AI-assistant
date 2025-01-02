import typing

import requests


class Weather:
    __api_key = "d53bf88d7eb131d05598464d6d2f10ee"

    @staticmethod
    def get_coordinates_for_city_name(
        city_name: str,
    ) -> typing.Tuple[float | None, float | None]:
        response = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&appid={Weather.__api_key}&limit=1"
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
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={Weather.__api_key}&units=metric&lang=en"
        )

        try:
            data = response.json()

            return data

        except:
            return None
