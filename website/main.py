import requests
from flask import (
    render_template,
    redirect,
    send_from_directory,
    json,
    request,
    url_for,
)
import os
from under_proxy import get_flask_app
import json

ON_SERVER = bool(os.environ.get("ON_SERVER"))
API_URL = "http://api:8000/" if ON_SERVER else "http://localhost:8000/"

app = get_flask_app()
print(ON_SERVER)


def api_request(method, endpoint, query_params={}, body={}):
    try:
        response = getattr(requests, method)(
            API_URL + endpoint, params=query_params, data=json.dumps(body)
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
    return None



@app.route("/")
def index():
    response = api_request("get", "user")
    print(response)
    return render_template("index.html", users=response)


@app.route("/add_user", methods=["POST"])
def add_user():
    data = {
        "email": request.form.get("email"),
        "password": request.form.get("password"),
        "name": request.form.get("name"),
        "lastname": request.form.get("lastname"),
        "phone_number": request.form.get("phone_number"),
        "user_role_name": request.form.get("user_role_name"),
    }

    api_request("post", "user", body=data)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
