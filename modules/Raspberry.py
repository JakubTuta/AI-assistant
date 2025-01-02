import requests


class Raspberry:
    __url = "http://localhost:2137"

    @staticmethod
    def toggle_led():  # -> Any:
        requests.get(f"{Raspberry.__url}/toggle_led")
