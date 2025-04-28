import threading
import typing

import flask

from .employer import Employer

app = flask.Flask(__name__)

employer: typing.Optional[Employer] = None

"""Buttons

        UP                      A
LEFT            RIGHT           B
        DOWN

"""

"""Buttons mapping
    A = speak
    B = help
    UP = volume up
    DOWN = volume down
    LEFT = previous song
    RIGHT = next song
"""


@app.route("/button-pressed/<key>/", methods=["GET"])
def button_pressed(key):
    print(f"Button {key} pressed.")

    if employer is not None:
        match key:
            case "A":
                employer.speak()

            case "B":
                Employer.help(audio=True)

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
        target=lambda: app.run(
            host="0.0.0.0", port=5000, debug=False, use_reloader=False
        )
    )
    threading_server.daemon = True
    threading_server.start()

    return threading_server


if __name__ == "__main__":
    start_app()
