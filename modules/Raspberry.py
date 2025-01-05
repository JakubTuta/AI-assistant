import requests


class Raspberry:
    _url = "http://localhost:2137"

    @staticmethod
    def toggle_led():  # -> Any:
        requests.get(f"{Raspberry._url}/toggle_led")
