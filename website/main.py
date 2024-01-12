import requests
from sqlalchemy.exc import NoResultFound
from flask import (
    render_template,
    redirect,
    send_from_directory,
    json,
    request,
    url_for,
    session,
    make_response,
    jsonify,
)
import os
from under_proxy import get_flask_app
from werkzeug.utils import secure_filename
from components import images_handler
from components import api_requests as API
from components import exceptions as exc
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


@app.context_processor
def company_data():
    try:
        footer_data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.COMPANY,
        )
    except API.APIError as e:
        LOGGER.error(e)
        footer_data = []
    
    return dict(footer_data=footer_data)


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
    return redirect(url_for("login"))


@app.route("/add_facility", methods=['GET'])
def add_facility_site():
    try:
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY_TYPE,
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template("add_facility.html", data=data)


@app.route("/add_facility", methods=['POST'])
def add_facility():
    try:
        facility_name = str(request.form.get("name"))
        description =  str(request.form.get("description"))
        price_hourly = int(request.form.get("price_hourly"))
        id_facility_type = int(request.form.get("id_facility_type"))
        city_name = str(request.form.get("city")).capitalize()
        street_name = str(request.form.get("street_name")).capitalize()
        state_name = str(request.form.get("state"))
        building_no = int(request.form.get("building_number"))
        postal_code = str(request.form.get("postal_code"))
        
        address = get_or_create_address(city_name, state_name, street_name, building_no, postal_code)

        try:  
            API.make_request(
                API.METHOD.POST,
                API.DATA_ENDPOINT.FACILITY,
                body = {
                    "name": facility_name,
                    "description": description,
                    "price_hourly": price_hourly,
                    "id_facility_type": id_facility_type,
                    "id_address": address[0]['id_address'],
                    "id_company": 1,
                    "ids_open_hours": [1], #zastanowic sie
                },)
        except:
            LOGGER.error("Nie mozna dodac obiektu")
            raise exc.UniqueConstraintViolated("Nie mozna dodac obiektu")
        
    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        return make_response(jsonify({"response": str(e)}), 404)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/my_account", methods=["GET"])
def my_account_site():
    return render_template("my_account.html")


@app.route("/admin_panel", methods=["GET"])
def admin_panel_site():
    return render_template("admin_panel.html")


@app.route("/edit_site", methods=["GET"])
def edit_site_site():
    return render_template("edit_site.html")


@app.route("/edit_site", methods=["POST"])
def edit_site():
    try: 
        company_name = str(request.form.get("name"))
        nip =  str(request.form.get("nip"))
        phone_number = str(request.form.get("phone_number"))
        city_name = str(request.form.get("city")).capitalize()
        street_name = str(request.form.get("street_name")).capitalize()
        state_name = str(request.form.get("state"))
        building_no = int(request.form.get("building_number"))
        postal_code = str(request.form.get("postal_code"))
        
        address = get_or_create_address(city_name, state_name, street_name, building_no, postal_code)

        try:  
            API.make_request(
                API.METHOD.PUT,
                API.DATA_ENDPOINT.COMPANY,
                query_params = {
                    "id_company": 1,
                    "name": company_name,
                    "nip": nip,
                    "phone_number": phone_number,
                    "id_address": address[0]['id_address'],
                },)
        except:
            LOGGER.error("Nie mozna zaktualizowac danych")
            raise exc.UniqueConstraintViolated("Nie mozna zaktualizowac danych")
        
    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        return make_response(jsonify({"response": str(e)}), 404)
    return make_response(jsonify({"response": "success"}), 200)


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


@app.route("/add", methods=["GET"])
def add():
    return make_response(jsonify({"response": "ok"}), 200)


def get_or_create_address(city_name, state_name, street_name, building_no, postal_code):
    try:
        API.make_request(API.METHOD.POST, API.DATA_ENDPOINT.CITY, body={"name": city_name})
        API.make_request(API.METHOD.POST, API.DATA_ENDPOINT.STATE, body={"name": state_name})
        print('a')
        LOGGER.info('a')
    except API.APIError as e:
        LOGGER.info(str(e))

    try:
        API.make_request(API.METHOD.POST, API.DATA_ENDPOINT.ADDRESS, body={
            "city_name": city_name,
            "state_name": state_name,
            "street_name": street_name,
            "building_number": building_no,
            "postal_code": postal_code,
        })
        print('a')
        LOGGER.info('a')
    except API.APIError as e:
        LOGGER.info("Address already exists")

    address = API.make_request(API.METHOD.GET, API.DATA_ENDPOINT.ADDRESS, query_params={
        "city_name": city_name,
        "state_name": state_name,
        "street_name": street_name,
        "building_number": building_no,
        "postal_code": postal_code,
    })

    return address


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
