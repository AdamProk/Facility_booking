import requests
from flask import (
    render_template,
    redirect,
    send_from_directory,
    json,
    request,
    url_for,
    session,
)
import os
from under_proxy import get_flask_app
from components import images_handler
import json

ON_SERVER = bool(os.environ.get("ON_SERVER"))
API_URL = "http://api:8000/" if ON_SERVER else "http://localhost:8000/"

app = get_flask_app()
app.secret_key = "secret"


def api_request(
    method, endpoint, query_params={}, body={}, headers=None, use_token=True
):
    try:
        if headers is None:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            if use_token:
                headers["Authorization"] = "Bearer " + session.get("token")
        response = getattr(requests, method)(
            API_URL + endpoint, params=query_params, data=body, headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
    return None


def get_token(email, password):
    data = {
        "grant_type": "",
        "username": str(request.form.get("email")),
        "password": str(request.form.get("password")),
        "scope": "",
        "client_id": "",
        "client_secret": "",
    }

    response = api_request("post", "token", body=data, use_token=False)
    if response is not None:
        token = response.get("access_token")
        session["token"] = token
        return token

    return None


@app.route("/")
def index():
    data = []
    if session.get("token"):
        data = api_request("get", "facility")
    return render_template("index.html", data=data)


@app.route("/login", methods=["POST"])
def login():
    email = (str(request.form.get("email")))
    password = (str(request.form.get("password")))
    print(get_token(email, password))

    return redirect(url_for("index"))


@app.route("/logout", methods=["GET"])
def logout():
    if session.get('token'):
        del session['token']
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
