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
import logging

LOGGER = logging.getLogger(__name__)

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
        LOGGER.error(e)
        data = []

    return render_template("home.html", data=data)

@app.route("/login", methods=["GET"])
def login_site():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = str(request.form.get("email"))
    password = str(request.form.get("password"))

    try:
        session["token"] = API.get_token(email, password)
    except API.APIError as e:
        LOGGER.error(e)

    return redirect(url_for("index"))


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("token", None)
    return redirect(url_for("index"))

@app.route("/addfacility", methods=['GET'])
def addfacility_site():
    try:
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY_TYPE,
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template("addfacility.html", data=data)

@app.route("/add_facility", methods=['POST'])
def add_facility():
  #id_facility = int(request.form.get("id_facility"))
    if not any(city['name'] == str(request.form.get("city")) for city in API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.CITY,)):
        API.make_request(API.METHOD.POST, API.DATA_ENDPOINT.CITY, body = { "name": str(request.form.get("city"))},)
    
    if not any(state['name'] == str(request.form.get("state")) for state in API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.STATE,)):
        API.make_request(API.METHOD.POST, API.DATA_ENDPOINT.STATE, body = { "name": str(request.form.get("state"))},)
    facility_name = str(request.form.get("name"))
    description =  str(request.form.get("description"))
    price_hourly = int(request.form.get("price_hourly"))
    id_facility_type = int(request.form.get("id_facility_type"))
    city_name = str(request.form.get("city")).capitalize()
    street_name = str(request.form.get("street_name")).capitalize()
    state_name = str(request.form.get("state"))
    building_no = int(request.form.get("building_number"))
    postal_code = str(request.form.get("postal_code"))

    cities = API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.CITY)

    try:
        for city in API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.CITY):
            print(city['name'])
            if city['name'] == city_name:
                id_city = city['id_city']
                print(id_city)
        if id_city == None:
            raise TypeError("City not found")
    except Exception as e:
        LOGGER.error(e)

    try:
        for states in API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.STATE):
            if states['name'] == state_name:
                id_state = states['id_state']
        if id_state == None:
            raise TypeError("State not found")
    except Exception as e:
        LOGGER.error(e)

    address_dic_criteria =  {
    "city": {
      "id_city": id_city,
      "name": city_name,
    },
    "state": {
      "id_state": id_state,
      "name": state_name,
    },
    "street_name": street_name,
    "building_number": building_no,
    "postal_code": postal_code
    }

    address_exists = any(all(d.get(key) == value for key, value in address_dic_criteria.items()) for d in API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.ADDRESS))

    if not address_exists:
        try:
            API.make_request(API.METHOD.POST, API.DATA_ENDPOINT.ADDRESS, body ={       
                "city_name": city_name,
                "state_name": state_name,
                "street_name": street_name,
                "building_number": building_no,
                "postal_code": postal_code,
            })
        except API.APIError as e:
            LOGGER.error(e)

    try:  
        for address in API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.ADDRESS,):
            print(address)
            print(address_dic_criteria)
            if all(address[key] == address_dic_criteria[key] for key in address_dic_criteria):
                id_address = address['id_address']
        if id_address == None:
            raise TypeError("Address not found")
    except Exception as e:
        LOGGER.error(e)

    try:
        API.make_request(
            API.METHOD.POST,
            API.DATA_ENDPOINT.FACILITY,
            body = {
                "name": facility_name,
                "description": description,
                "price_hourly": price_hourly,
                "id_facility_type": id_facility_type,
                "id_address": id_address,
                "id_company": 1,
                "ids_open_hours": [1], #zastanowic sie
            },)
    except API.APIError as e:
        LOGGER.error(e)

    return redirect(url_for("index"))

@app.route("/upload_facility_image", methods=["POST"])
def upload_facility_image():
    id_facility = int(request.form.get("id_facility"))
    if "file" not in request.files:
        LOGGER.error("No file passed.")
        return redirect(url_for("index"))

    file = request.files["file"]
    try:
        image_rel_path = images_handler.upload_image(file)

    except images_handler.ImageHandlerError as e:
        LOGGER.error("Error uploading image: " + str(e))
        return redirect(url_for("index"))

    try:
        API.make_request(
            API.METHOD.POST,
            API.DATA_ENDPOINT.IMAGE,
            body={
                "image_path": image_rel_path,
                "id_facility": id_facility,
            },
        )
    except API.APIError as e:
        try:
            images_handler.remove_image(image_rel_path)
        except images_handler.ImageHandlerError:
            LOGGER.error("Failed to remove the image.")
        LOGGER.error(
            "Failed to put image in the database. It was removed from images folder." + str(e)
        )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
