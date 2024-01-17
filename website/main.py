import requests
import traceback
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


# region HOME


@app.route("/", methods=["GET"], redirect_url="/error")
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


@app.route("/search_facility", methods=["GET"])
def search_facility():
    try:
        search_term = request.args.get('query', '')
        if not search_term:
            query_params = None
        else:
            query_params = {'name': search_term}
        results  = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY,
            query_params=query_params
        )
    except API.APIError as e:
        LOGGER.error(e)
        results  = []

    return render_template("search_results.html", results=results )


# endregion HOME


# region CONTEXT PROCESSORS


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


@app.context_processor
def user_data():
    try:
        user_data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.ME,
        )
    except API.APIError as e:
        LOGGER.error(e)
        user_data = dict()

    return dict(user_data=user_data)

app.user_data = user_data

# endregion CONTEXT PROCESSORS


# region LOGIN


@app.route("/login", methods=["GET"])
def login_site():
    # CHECKER = CHECK_IF_NO_SESSION()
    # if CHECKER:
    #     return CHECKER
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    CHECKER = CHECK_IF_NO_SESSION()
    if CHECKER:
        return CHECKER
    email = str(request.form.get("email"))
    password = str(request.form.get("password"))

    try:
        session["token"] = API.get_token(email, password)
    except API.APIError as e:
        LOGGER.info(e)
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": "Incorrect email or password"}), 401)
    
    return make_response(jsonify({"response": "Successfully logged in."}), 200)


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("token", None)
    return redirect(url_for("login"))


# endregion LOGIN


# region REGISTER


@app.route("/register", methods=["GET"])
def register_site():
    CHECKER = CHECK_IF_NO_SESSION()
    if CHECKER:
        return CHECKER
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    CHECKER = CHECK_IF_NO_SESSION()
    if CHECKER:
        return CHECKER
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
            msg = "You have successfully registered!"
        except API.APIError as e:
            LOGGER.info(e)
            return make_response(jsonify({"response": str(e)}), 500)
    else:
        LOGGER.info("No parameter found..")
        msg = "Account already exists!"
    return make_response(jsonify({"response": msg}), 200)


# endregion REGISTER


# region FACILITY


@app.route("/add_facility", methods=["GET"])
def add_facility_site():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
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
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
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

        monday = get_or_create_open_hours("Monday", str(request.form.get("monday_start")), str(request.form.get("monday_end")))
        tuesday = get_or_create_open_hours("Tuesday", str(request.form.get("tuesday_start")), str(request.form.get("tuesday_end")))
        wednesday = get_or_create_open_hours("Wednesday", str(request.form.get("wednesday_start")), str(request.form.get("wednesday_end")))
        thursday = get_or_create_open_hours("Thursday", str(request.form.get("thursday_start")), str(request.form.get("thursday_end")))
        friday = get_or_create_open_hours("Friday", str(request.form.get("friday_start")), str(request.form.get("friday_end")))
        saturday = get_or_create_open_hours("Saturday", str(request.form.get("saturday_start")), str(request.form.get("saturday_end")))
        sunday = get_or_create_open_hours("Sunday", str(request.form.get("sunday_start")), str(request.form.get("sunday_end")))

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
                    "ids_open_hours": [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Can't add the facility")
            raise exc.UniqueConstraintViolated("Can't add the facility")

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/upload_facility_image", methods=["POST"])
def upload_facility_image():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
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
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
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
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
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

        address = get_or_create_address(
            city_name, state_name, street_name, building_no, postal_code
        )

        monday = get_or_create_open_hours("Monday", str(request.form.get("monday_start")), str(request.form.get("monday_end")))
        tuesday = get_or_create_open_hours("Tuesday", str(request.form.get("tuesday_start")), str(request.form.get("tuesday_end")))
        wednesday = get_or_create_open_hours("Wednesday", str(request.form.get("wednesday_start")), str(request.form.get("wednesday_end")))
        thursday = get_or_create_open_hours("Thursday", str(request.form.get("thursday_start")), str(request.form.get("thursday_end")))
        friday = get_or_create_open_hours("Friday", str(request.form.get("friday_start")), str(request.form.get("friday_end")))
        saturday = get_or_create_open_hours("Saturday", str(request.form.get("saturday_start")), str(request.form.get("saturday_end")))
        sunday = get_or_create_open_hours("Sunday", str(request.form.get("sunday_start")), str(request.form.get("sunday_end")))

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
                    "ids_open_hours": [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Can't edit the facility")
            raise exc.UniqueConstraintViolated("Can't edit the facility")

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/delete_facility", methods=["POST"])
def delete_facility():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
    id_facility = int(request.form.get("id_facility"))
    try:
        API.make_request(
            API.METHOD.DELETE,
            API.DATA_ENDPOINT.FACILITY,
            query_params={"facility_id": id_facility},
        )
    except API.APIError as e:
        LOGGER.info(e)
        raise exc.UniqueConstraintViolated("Couldn't delete the facility")

    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)

    return redirect(url_for("index"))


# endregion FACILITY


# region MY ACCOUNT


@app.route("/my_account", methods=["GET"])
def my_account_site():
    CHECKER = CHECK_IF_LOGGED_IN()
    if CHECKER:
        return CHECKER
    return render_template("my_account.html")

@app.route("/edit_account_info", methods=["PUT"])
def edit_account_info():
    CHECKER = CHECK_IF_LOGGED_IN()
    if CHECKER:
        return CHECKER
    try:
        name = str(request.form.get("name"))
        lastname = str(request.form.get("lastname"))
        phone_number = str(request.form.get("phone_number"))
        try:
            API.make_request(
                API.METHOD.PUT,
                API.DATA_ENDPOINT.ME,
                query_params={
                    "name": name,
                    "lastname": lastname,
                    "phone_number": phone_number,
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Couldn't edit user info. Try again.")
            raise exc.UniqueConstraintViolated("Couldn't edit user info. Try again.")
        
    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)

   
# endregion MY ACCOUNT

# region RESETTING PASSWORD

@app.route("/reset_password", methods=["GET"])
def reset_password_site():
    CHECKER = CHECK_IF_LOGGED_IN()
    if CHECKER:
        return CHECKER
    return render_template("reset_password.html")

@app.route("/reset_password", methods=["POST"])
def reset_password():
    CHECKER = CHECK_IF_LOGGED_IN()
    if CHECKER:
        return CHECKER
    try: 
        old_password = str(request.form.get("old_password"))
        new_password = str(request.form.get("new_password"))
        repeat_password = str(request.form.get("repeat_password"))
        if repeat_password != new_password:
            raise exc.UniqueConstraintViolated("Passwords don't match.")
    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)


# endregion RESETTING PASSWORD

# region ADMIN PANEL


@app.route("/admin_panel", methods=["GET"])
def admin_panel_site():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
    return render_template("admin_panel.html")


# region EDIT SITE


@app.route("/edit_site", methods=["GET"])
def edit_site_site():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
    return render_template("edit_site.html")


@app.route("/edit_site", methods=["POST"])
def edit_site():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
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
            LOGGER.error("Couldn't edit site info. Try again.")
            raise exc.UniqueConstraintViolated("Couldn't edit site info. Try again.")

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": "API ERROR"}), 500)
    except ValueError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    CHECKER = CHECK_IF_ADMIN_STATUS()
    if CHECKER:
        return CHECKER
    if "file" not in request.files:
        LOGGER.error("No file passed.")
        return make_response(jsonify({"response": "404"}), 404)

    try:
        file = request.files["file"]
        if file.filename == "":
            raise images_handler.ImageHandlerError("Please upload an image")
        else:
            file.filename = 'logo.png'
    except images_handler.ImageHandlerError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    
    try:
        images_handler.upload_image(file)

    except images_handler.ImageHandlerError as e:
        LOGGER.error("Error uploading image: " + str(e))
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)

    return make_response(jsonify({"response": "Logo Uploaded Successfully"}), 200)


# endregion EDIT SITE

# endregion ADMIN PANEL


# region ACTIONS


def get_or_create_address(city_name, state_name, street_name, building_no, postal_code):
    CHECKER = CHECK_IF_LOGGED_IN()
    if CHECKER:
        return CHECKER
    try:
        API.make_request(
            API.METHOD.POST, API.DATA_ENDPOINT.CITY, body={"name": city_name}
        )
        API.make_request(
            API.METHOD.POST, API.DATA_ENDPOINT.STATE, body={"name": state_name}
        )
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
            raise ValueError("Inappropriate Address")
    except ValueError as e:
        raise e

    return address

def CHECK_IF_LOGGED_IN():
    try:
        if(session.get('token') is None):
            return redirect(url_for("index"))
    except Exception as e:
        make_response(jsonify({"response": "Something went wrong with checking your logged in status. Error:" + str(e)}), 500)

def CHECK_IF_ADMIN_STATUS():
    try:
        if(session.get('token') is None or user_data()['user_data']['user_role']['name'] != "Admin"):
            return redirect(url_for("index"))
    except Exception as e:
        make_response(jsonify({"response": "Something went wrong with checking your admin privileges. Error:" + str(e)}), 500)

def CHECK_IF_NO_SESSION(): 
    try:
        if(session.get("token") is not None):
            return redirect(url_for("index"))
    except Exception as e:
        make_response(jsonify({"response": "Something went wrong with checking your logged out status. Error:" + str(e)}), 500)

def get_or_create_open_hours(day_name, start_hour, end_hour):
    try:
        API.make_request(
            API.METHOD.POST,
            API.DATA_ENDPOINT.OPEN_HOUR,
            body={
                "day_name": day_name,
                "start_hour": start_hour,
                "end_hour": end_hour,
            },
        )
    except API.APIError as e:
        LOGGER.error("Hours already exists")

    try:
        open_hours = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.OPEN_HOUR,
            query_params={
                "day_name": day_name,
                "start_hour": start_hour,
                "end_hour": end_hour,
            },
        )
        if not open_hours:
            raise ValueError("Inappropriate Hours")
    except ValueError as e:
        raise e

    return open_hours[0]["id_open_hours"]

# endregion ACTIONS


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
