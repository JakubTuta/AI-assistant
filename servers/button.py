import threading
import typing

import flask

from modules.employer import Employer

app = flask.Flask(__name__)

employer: typing.Optional[Employer] = None

"""Buttons

         UP                     A
LEFT            RIGHT           B
        DOWN

"""

"""Buttons mapping
    A = speak
    B = toggle playback
    UP = volume up
    DOWN = volume down
    LEFT = previous song
    RIGHT = next song
"""


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


@app.route("/ping", methods=["GET"])
def ping():
    return flask.jsonify({"status": "ok"})


@app.route("/button-pressed/<key>/", methods=["GET"])
def button_pressed(key):
    if employer is not None:
        employer._refresh_available_jobs()

        match key:
            case "A":
                employer.speak()

            case "B":
                if function := employer.available_jobs.get("toggle_playback"):
                    function()

            case "UP":
                if function := employer.available_jobs.get("volume_up"):
                    function()

            case "DOWN":
                if function := employer.available_jobs.get("volume_down"):
                    function()

            case "LEFT":
                if function := employer.available_jobs.get("previous_song"):
                    function()

            case "RIGHT":
                if function := employer.available_jobs.get("next_song"):
                    function()

    return flask.jsonify({"status": "success", "message": f"Button {key} pressed."})


def start_app(employer_instance=None):
    global employer
    employer = employer_instance

    threading_server = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5001, debug=False)
    )
    threading_server.daemon = True
    threading_server.start()

    return threading_server


if __name__ == "__main__":
    start_app()
