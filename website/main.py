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
import traceback


LOGGER = logging.getLogger(__name__)

app = get_flask_app()
app.secret_key = "secret"
app.config["UPLOAD_FOLDER"] = images_handler.IMAGES_DIR


@app.route("/", methods=["GET"])
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
            query_params={"id_company": 1}
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


@app.route("/register", methods=["GET"])
def register_site():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    msg = ""
    email = str(request.form["email"])
    password = str(request.form["password"])
    username = str(request.form["username"])
    lastname = str(request.form["lastname"])
    phone_number = str(request.form["phone_number"])
    try:
        account = API.make_request(
            API.METHOD.GET,
            API.ACTION_ENDPOINT.CHECK_IF_EMAIL_EXISTS,
            query_params={"email": email},
            get_token_from_session=False,
        )[
            "result"
        ]  # TOCHANGE
    except API.APIError as e:
        LOGGER.info(e)
        return make_response(jsonify({"response": str(e)}), 500)

    if not account:
        try:
            API.make_request(
                API.METHOD.POST,
                API.DATA_ENDPOINT.USER,
                body={
                    "email": email,
                    "password": password,
                    "name": username,
                    "lastname": lastname,
                    "phone_number": phone_number,
                    "user_role_name": "User",
                },
                get_token_from_session=False,
            )
            msg = "You have successfully registered !"
        except API.APIError as e:
            LOGGER.info(e)
            return make_response(jsonify({"response": str(e)}), 500)
    else:
        LOGGER.info("No parameter found..")
        msg = "Account already exists!"
    return make_response(jsonify({"response": msg}), 200)


@app.route("/add_facility", methods=["GET"])
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


@app.route("/add_facility", methods=["POST"])
def add_facility():
    try:
        facility_name = str(request.form.get("name"))
        description = str(request.form.get("description"))
        price_hourly = int(request.form.get("price_hourly"))
        id_facility_type = int(request.form.get("id_facility_type"))
        city_name = str(request.form.get("city")).capitalize()
        street_name = str(request.form.get("street_name")).capitalize()
        state_name = str(request.form.get("state"))
        building_no = int(request.form.get("building_number"))
        postal_code = str(request.form.get("postal_code"))

        address = get_or_create_address(
            city_name, state_name, street_name, building_no, postal_code
        )

        try:
            API.make_request(
                API.METHOD.POST,
                API.DATA_ENDPOINT.FACILITY,
                body={
                    "name": facility_name,
                    "description": description,
                    "price_hourly": price_hourly,
                    "id_facility_type": id_facility_type,
                    "id_address": address[0]["id_address"],
                    "id_company": 1,
                    "ids_open_hours": [1],  # zastanowic sie
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Nie mozna dodac obiektu")
            raise exc.UniqueConstraintViolated("Nie mozna dodac obiektu")

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
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
        nip = str(request.form.get("nip"))
        phone_number = str(request.form.get("phone_number"))
        city_name = str(request.form.get("city")).capitalize()
        street_name = str(request.form.get("street_name")).capitalize()
        state_name = str(request.form.get("state"))
        building_no = int(request.form.get("building_number"))
        postal_code = str(request.form.get("postal_code"))

        address = get_or_create_address(
            city_name, state_name, street_name, building_no, postal_code
        )

        try:
            API.make_request(
                API.METHOD.PUT,
                API.DATA_ENDPOINT.COMPANY,
                query_params={
                    "id_company": 1,
                    "name": company_name,
                    "nip": nip,
                    "phone_number": phone_number,
                    "id_address": address[0]["id_address"],
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Nie mozna dodac obiektu")
            raise exc.UniqueConstraintViolated("Nie mozna dodac obiektu")

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    if "file" not in request.files:
        LOGGER.error("No file passed.")
        return make_response(jsonify({"response": "404"}), 404)

    try:
        file = request.files["file"]
        if file.filename == "":
            raise images_handler.ImageHandlerError("Nie podałeś zdjęcia")
        else:
            file.filename = 'logo.png'
    except images_handler.ImageHandlerError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
    
    try:
        images_handler.upload_image(file)

    except images_handler.ImageHandlerError as e:
        LOGGER.error("Error uploading image: " + str(e))
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)

    return make_response(jsonify({"response": "Logo Uploaded Successfully"}), 200)


@app.route("/upload_facility_image", methods=["POST"])
def upload_facility_image():
    LOGGER.error(request.files)
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
            "Failed to put image in the database. It was removed from images folder."
            + str(e)
        )

    return redirect(url_for("index"))


@app.route("/edit_facility", methods=["GET"])
def edit_facility_site():
    try:
        id_facility = int(request.args.get("id_facility"))
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY,
            query_params={'id_facility': id_facility},
        )
        data_fac_type = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY_TYPE
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template("edit_facility.html", data=data, data_fac_type=data_fac_type)


@app.route("/edit_facility", methods=["POST"])
def edit_facility():
    try:
        id_facility = int(request.form.get("id_facility"))
        facility_name = str(request.form.get("name"))
        description = str(request.form.get("description"))
        price_hourly = str(request.form.get("price_hourly"))
        price_hourly = price_hourly.replace(',', '.')
        price_hourly = int(float(price_hourly))
        id_facility_type = int(request.form.get("id_facility_type"))
        city_name = str(request.form.get("city")).capitalize()
        street_name = str(request.form.get("street_name")).capitalize()
        state_name = str(request.form.get("state"))
        building_no = int(request.form.get("building_number"))
        postal_code = str(request.form.get("postal_code"))

        LOGGER.error(id_facility_type)

        address = get_or_create_address(
            city_name, state_name, street_name, building_no, postal_code
        )

        try:
            API.make_request(
                API.METHOD.PUT,
                API.DATA_ENDPOINT.FACILITY,
                query_params={
                    "id_facility": id_facility,
                    "name": facility_name,
                    "description": description,
                    "price_hourly": price_hourly,
                    "id_facility_type": id_facility_type,
                    "id_address": address[0]["id_address"],
                    "id_company": 1,
                    "ids_open_hours": [1],  # zastanowic sie
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Nie mozna dodac obiektu")
            raise exc.UniqueConstraintViolated("Nie mozna dodac obiektu")

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc());
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/delete_facility", methods=["POST"])
def delete_facility():
    id_facility = int(request.form.get("id_facility"))
    try:
        API.make_request(
            API.METHOD.DELETE,
            API.DATA_ENDPOINT.FACILITY,
            query_params={"facility_id": id_facility},
        )
    except API.APIError as e:
        LOGGER.info(e)
        raise exc.UniqueConstraintViolated("Nie udalo sie usunac danego obiektu")

    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)

    return redirect(url_for("index"))


def get_or_create_address(city_name, state_name, street_name, building_no, postal_code):
    try:
        API.make_request(
            API.METHOD.POST, API.DATA_ENDPOINT.CITY, body={"name": city_name}
        )
        API.make_request(
            API.METHOD.POST, API.DATA_ENDPOINT.STATE, body={"name": state_name}
        )
        print("a")
        LOGGER.info("a")
    except API.APIError as e:
        LOGGER.error(str(e))

    try:
        API.make_request(
            API.METHOD.POST,
            API.DATA_ENDPOINT.ADDRESS,
            body={
                "city_name": city_name,
                "state_name": state_name,
                "street_name": street_name,
                "building_number": building_no,
                "postal_code": postal_code,
            },
        )
    except API.APIError as e:
        LOGGER.error("Address already exists")

    try:
        address = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.ADDRESS,
            query_params={
                "city_name": city_name,
                "state_name": state_name,
                "street_name": street_name,
                "building_number": building_no,
                "postal_code": postal_code,
            },
        )
        if not address:
            raise ValueError("Inapproperiate Address")
    except ValueError as e:
        raise e

    return address


@app.route("/register_acc", methods=["GET"])
def register_acc():
    return make_response(
        jsonify({"response": "heck yeah"}), 200
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
