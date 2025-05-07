import os

import requests


class News:
    api_key = os.getenv("NEWS_API_KEY", None)

    @staticmethod
    def get_today_news():
        url = "https://newsapi.org/v2/everything"

        data = {
            "country": "pl",
            "apiKey": News.api_key,
        }

        response = requests.get(url, params=data)

        print(response.json)
