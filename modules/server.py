import flask

app = flask.Flask(__name__)


@app.route("/talk", methods=["GET"])
def talk():
    return flask.jsonify({"message": "Hello from the /talk endpoint!"})


def start_app():
    app.run(debug=True, host="0.0.0.0", port=5000)
