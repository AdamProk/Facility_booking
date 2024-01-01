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
from werkzeug.utils import secure_filename
from components import images_handler
from components import api_requests as API
import json

app = get_flask_app()
app.secret_key = "secret"
app.config["UPLOAD_FOLDER"] = images_handler.IMAGES_DIR


@app.route("/", methods=["GET", "POST"])
def index():
    try:
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY,
        )
    except API.APIError as e:
        print(e)
        data = []

    return render_template("index.html", data=data)


@app.route("/login", methods=["POST"])
def login():
    email = str(request.form.get("email"))
    password = str(request.form.get("password"))

    try:
        session["token"] = API.get_token(email, password)
    except API.APIError as e:
        print(e)

    return redirect(url_for("index"))


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("token", None)
    return redirect(url_for("index"))


@app.route("/upload_facility_image", methods=["POST"])
def upload_facility_image():
    id_facility = int(request.form.get("id_facility"))
    if "file" not in request.files:
        print("No file passed.")
        return redirect(url_for("index"))

    file = request.files["file"]
    try:
        image_path = images_handler.upload_image(file)

    except Exception as e:
        print("Error uploading image: " + str(e))
        return redirect(url_for("index"))

    try:
        API.make_request(
            API.METHOD.POST,
            API.DATA_ENDPOINT.IMAGE,
            body={
                "image_path": "adsgashawg",
                "id_facility": id_facility,
            },
        )
    except API.APIError as e:
        print(e)
        try:
            images_handler.remove_image(image_path)
        except images_handler.ImageHandlerError:
            print("Failed to remove the image.")
        print(
            "Failed to put image in the database. It was removed from images folder."
        )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
