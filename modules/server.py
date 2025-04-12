import flask

app = flask.Flask(__name__)


@app.route("/button-pressed/<key>/", methods=["GET"])
def button_pressed(key):
    return f"Button pressed: {key}"


def start_app():
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    start_app()
