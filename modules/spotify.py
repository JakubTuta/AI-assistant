import base64
import datetime
import http.server
import os
import socketserver
import threading
import typing
import urllib.parse
import webbrowser

import requests

from helpers.cache import Cache


class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code

        # Parse the query parameters
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        if "code" in query_components:
            auth_code = query_components["code"][0]

            # Send a simple response back to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication successful!</h1><p>You can close this window now.</p></body></html>"
            )

            # Signal the server to shut down
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication failed</h1></body></html>"
            )


class Spotify:
    ENV_SPOTIFY_CLIENT_ID = "SPOTIFY_CLIENT_ID"
    ENV_SPOTIFY_CLIENT_SECRET = "SPOTIFY_CLIENT_SECRET"

    SPOTIFY_OAUTH_ACCESS_KEY = "SPOTIFY_OAUTH_ACCESS_KEY"
    SPOTIFY_OAUTH_REFRESH_KEY = "SPOTIFY_OAUTH_REFRESH_KEY"
    SPOTIFY_OAUTH_EXPIRATION_DATE = "SPOTIFY_OAUTH_EXPIRATION_DATE"

    PORT = 8888
    REDIRECT_URI = f"http://127.0.0.1:{PORT}/callback"

    SCOPE = "user-read-playback-state user-modify-playback-state"

    def __init__(self):
        self.client_id = os.getenv(Spotify.ENV_SPOTIFY_CLIENT_ID, None)
        self.client_secret = os.getenv(Spotify.ENV_SPOTIFY_CLIENT_SECRET, None)

        if self.client_id is None or self.client_secret is None:
            raise Exception(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in environment variables"
            )

        self.access_token, self.refresh_token = self._get_tokens_from_cache()

        if self.access_token is not None and self.refresh_token is not None:
            self.device_id = self._get_active_devices()

            return

        self.auth_code = self._get_auth_code()
        if self.auth_code is None:
            raise Exception("Failed to get authorization code")

        self.access_token, self.refresh_token = self._get_tokens()
        if self.access_token is None or self.refresh_token is None:
            raise Exception("Failed to get access token and refresh token")

        self.device_id = self._get_active_devices()

    def toggle_playback(self):
        """
        Toggle Spotify music playback state between play and pause.
        """

        is_playing = self._is_playback_playing()

        if is_playing:
            self.stop_playback()

        else:
            self.resume_playback()

    def resume_playback(self):
        """
        Resume Spotify music playback.
        """

        url = "https://api.spotify.com/v1/me/player/play"

        if self.device_id:
            url += f"?device_id={self.device_id}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        response = requests.put(url, headers=headers)

        if response.status_code == 200:
            print("Playback resumed successfully")

        elif response.status_code == 401:
            print("Access token expired, refreshing...")
            self._refresh_access_token(self.refresh_token)
            self.resume_playback()

        else:
            print(f"Failed to resume playback: {response.status_code}")
            print(response.text)

    def stop_playback(self):
        """
        Pause Spotify music playback.
        """

        url = "https://api.spotify.com/v1/me/player/pause"

        if self.device_id:
            url += f"?device_id={self.device_id}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        response = requests.put(url, headers=headers)

        if response.status_code == 200:
            print("Playback paused successfully")

        elif response.status_code == 401:
            print("Access token expired, refreshing...")
            self._refresh_access_token(self.refresh_token)
            self.stop_playback()

        else:
            print(f"Failed to pause playback: {response.status_code}")
            print(response.text)

    def _is_playback_playing(self):
        playback_state = self._get_playback_state()

        if playback_state and "is_playing" in playback_state:
            return playback_state["is_playing"]

        return False

    def _get_playback_state(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 204:
            return {"error": "No active device found"}

        else:
            print(f"Failed to get playback state: {response.status_code}")
            print(response.text)

            return None

    def _get_active_devices(self) -> typing.Optional[str]:
        url = "https://api.spotify.com/v1/me/player/devices"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url, headers=headers)
        print(response)

        if response.status_code == 200 and len(response.json()["devices"]) > 0:
            active_device = next(
                (
                    device
                    for device in response.json()["devices"]
                    if device["is_active"]
                ),
                None,
            )

            if active_device is None:
                active_device = response.json()["devices"][0]

            return active_device.get("id", None)

        elif response.status_code == 401:
            print("Access token expired, refreshing...")
            self._refresh_access_token(self.refresh_token)
            self._get_active_devices()

        else:
            print(f"Failed to get active devices: {response.status_code}")

            return None

    def _refresh_access_token(self, refresh_token):
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        response = requests.post(
            "https://accounts.spotify.com/api/token", headers=headers, data=data
        )

        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]

            return token_info["access_token"]

        else:
            print(f"Failed to refresh token: {response.status_code}")
            print(response.text)
            self.access_token = None

            return None

    def _get_tokens_from_cache(self):
        access_token = Cache.get_value(Spotify.SPOTIFY_OAUTH_ACCESS_KEY)
        refresh_token = Cache.get_value(Spotify.SPOTIFY_OAUTH_REFRESH_KEY)
        expiration_date = Cache.get_value(Spotify.SPOTIFY_OAUTH_EXPIRATION_DATE)

        if access_token and refresh_token and expiration_date:
            try:
                expiration_datetime = datetime.datetime.fromisoformat(expiration_date)

                if expiration_datetime > datetime.datetime.now():
                    return access_token, refresh_token

                else:
                    access_token = self._refresh_access_token(refresh_token)

                    if access_token:
                        return access_token, refresh_token

            except (ValueError, TypeError):
                pass

        return None, None

    def _get_auth_code(self):
        auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": Spotify.REDIRECT_URI,
                "scope": Spotify.SCOPE,
                "show_dialog": "true",
            }
        )

        print(f"Opening browser for authorization: {auth_url}")
        webbrowser.open(auth_url)

        httpd = socketserver.TCPServer(("", Spotify.PORT), AuthHandler)
        print(f"Waiting for authorization at http://localhost:{Spotify.PORT}")
        httpd.serve_forever()

        if auth_code:
            print("Authorization code received")

            return auth_code

        else:
            print("Failed to get authorization code")

            return None

    def _get_tokens(self):
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": Spotify.REDIRECT_URI,
        }

        response = requests.post(
            "https://accounts.spotify.com/api/token", headers=headers, data=data
        )

        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]
            self.refresh_token = token_info["refresh_token"]
            self._save_tokens(self.access_token, self.refresh_token)

            return token_info["access_token"], token_info["refresh_token"]

        else:
            print(f"Failed to get tokens: {response.status_code}")
            print(response.text)
            self.access_token = None
            self.refresh_token = None

            return None, None

    def _save_tokens(self, access_token, refresh_token):
        expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=3600)
        Cache.set_value(Spotify.SPOTIFY_OAUTH_ACCESS_KEY, access_token)
        Cache.set_value(Spotify.SPOTIFY_OAUTH_REFRESH_KEY, refresh_token)
        Cache.set_value(
            Spotify.SPOTIFY_OAUTH_EXPIRATION_DATE, expiration_date.isoformat()
        )
