import threading
import typing

import flask
import yaml

from modules.employer import Employer

app = flask.Flask(__name__)

employer: typing.Optional[Employer] = None


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


@app.route("/ping", methods=["GET"])
def ping():
    return flask.jsonify({"status": "ok"})


@app.route("/commands", methods=["GET"])
def get_commands():
    with open("commands.yaml", "r") as file:
        commands_data = yaml.safe_load(file)

    return flask.jsonify(commands_data), 200


@app.route("/<job_name>", methods=["POST"])
def execute_job(job_name):
    if not employer:
        return (
            flask.jsonify({"status": "error", "message": "Employer not initialized"}),
            500,
        )

    employer._refresh_available_jobs()

    if job_name in employer.available_jobs:
        job = employer.available_jobs[job_name]
        kwargs = flask.request.args.to_dict()
        result = job(**kwargs)

        return flask.jsonify({"status": "success", "result": result}), 200

    else:
        return flask.jsonify({"status": "error", "message": "Job not found"}), 404


def start_app(employer_instance=None):
    print(employer_instance)
    global employer
    employer = employer_instance

    threading_server = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5002, debug=False)
    )
    threading_server.daemon = True
    threading_server.start()

    return threading_server
