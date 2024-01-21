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
from datetime import date, datetime, timedelta
from components import images_handler
from components import api_requests as API
from components import exceptions as exc
import json
import logging
import traceback
from datetime import date, datetime, timedelta
from components import email_handler

LOGGER = logging.getLogger(__name__)

app = get_flask_app()
app.secret_key = "secret"
app.config["UPLOAD_FOLDER"] = images_handler.IMAGES_DIR


# region HOME


@app.route("/", methods=["GET"], logged_in=True, redirect_url="/login")
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


@app.route("/search_facility", methods=["GET"], logged_in=True)
def search_facility():
    try:
        query = request.args.get("query")
        LOGGER.error(query)
        if not query:
            query_params = None
        else:
            query_params = {'name': query,
                            'description': query}
        results  = API.make_request(
            API.METHOD.GET,
            API.ACTION_ENDPOINT.SEARCH_FACILITY,
            query_params=query_params
        )
    except API.APIError as e:
        LOGGER.error(e)
        results  = []

    return render_template("search_results.html", results=results)

# endregion HOME


# region CONTEXT PROCESSORS


@app.context_processor
def company_data():
    try:
        footer_data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.COMPANY,
            query_params={"id_company": 1},
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
    return render_template("login.html")


@app.route("/login", logged_in=False, redirect_url="/", methods=["POST"])
def login():
    email = str(request.form.get("email"))
    password = str(request.form.get("password"))
    try:
        session["token"] = API.get_token(email, password)
    except API.APIError as e:
        LOGGER.info(e)
        LOGGER.error(traceback.format_exc())
        return make_response(
            jsonify({"response": "Incorrect email or password"}), 401
        )

    return make_response(jsonify({"response": "Successfully logged in."}), 200)


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("token", None)
    return redirect(url_for("login"))


# endregion LOGIN


# region REGISTER


@app.route("/register", methods=["GET"], logged_in=False, redirect_url="/")
def register_site():
    return render_template("register.html")


@app.route("/register", methods=["POST"], logged_in=False, redirect_url="/")
def register():
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
    except (API.APIError, IndexError) as e:
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
        except API.APIError as e:
            LOGGER.info(e)
            return make_response(jsonify({"response": "API_ERROR"}), 500)
    else:
        LOGGER.info("No parameter found..")
        return make_response(jsonify({"response": "Such account already exists!"}), 200)
    
    email_data={
        "title": "Facility Booking - Registration of your account",
        "body": "Welcome " + username + "<br><br>Thanks for registering to our website!",
    }
    email_handler.send_notification(email_data)
    return make_response(jsonify({"response": "You have successfully registered!"}), 200)



# endregion REGISTER


# region FACILITY


@app.route("/add_facility", methods=["GET"], admin=True, redirect_url="/")
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


@app.route("/add_facility", methods=["POST"], admin=True, redirect_url="/")
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

        monday = get_or_create_open_hours(
            "Monday",
            str(request.form.get("monday_start")),
            str(request.form.get("monday_end")),
        )
        tuesday = get_or_create_open_hours(
            "Tuesday",
            str(request.form.get("tuesday_start")),
            str(request.form.get("tuesday_end")),
        )
        wednesday = get_or_create_open_hours(
            "Wednesday",
            str(request.form.get("wednesday_start")),
            str(request.form.get("wednesday_end")),
        )
        thursday = get_or_create_open_hours(
            "Thursday",
            str(request.form.get("thursday_start")),
            str(request.form.get("thursday_end")),
        )
        friday = get_or_create_open_hours(
            "Friday",
            str(request.form.get("friday_start")),
            str(request.form.get("friday_end")),
        )
        saturday = get_or_create_open_hours(
            "Saturday",
            str(request.form.get("saturday_start")),
            str(request.form.get("saturday_end")),
        )
        sunday = get_or_create_open_hours(
            "Sunday",
            str(request.form.get("sunday_start")),
            str(request.form.get("sunday_end")),
        )

        try:
            fac = API.make_request(
                API.METHOD.POST,
                API.DATA_ENDPOINT.FACILITY,
                body={
                    "name": facility_name,
                    "description": description,
                    "price_hourly": price_hourly,
                    "id_facility_type": id_facility_type,
                    "id_address": address[0]["id_address"],
                    "id_company": 1,
                    "ids_open_hours": [
                        monday,
                        tuesday,
                        wednesday,
                        thursday,
                        friday,
                        saturday,
                        sunday,
                    ],
                },
            )
        except exc.UniqueConstraintViolated as e:
            LOGGER.error("Can't add the facility")
            raise exc.UniqueConstraintViolated("Can't add the facility")

        if "files" not in request.files or not request.files["files"].filename:
            LOGGER.info("No images passed.")
            return make_response(
                jsonify({"response": "success, no images added"}), 200
            )

        try:
            files = request.files.getlist("files")
            for file in files:
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
                            "id_facility": fac["id_facility"],
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
        except images_handler.ImageHandlerError as e:
            LOGGER.error("Error uploading image: " + str(e))
            LOGGER.error(traceback.format_exc())
            return make_response(jsonify({"response": str(e)}), 500)

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


@app.route(
    "/upload_facility_image", methods=["POST"], admin=True, redirect_url="/"
)
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
            "Failed to put image in the database. It was removed from images folder."
            + str(e)
        )

    return redirect(url_for("index"))


@app.route("/edit_facility", methods=["GET"], admin=True, redirect_url="/")
def edit_facility_site():
    try:
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY,
            query_params={"id_facility": int(request.args.get("id_facility"))},
        )
        data_fac_type = API.make_request(
            API.METHOD.GET, API.DATA_ENDPOINT.FACILITY_TYPE
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template(
        "edit_facility.html", data=data, data_fac_type=data_fac_type
    )


@app.route("/edit_facility", methods=["POST"], admin=True, redirect_url="/")
def edit_facility():
    try:
        id_facility = int(request.form.get("id_facility"))
        facility_name = str(request.form.get("name"))
        description = str(request.form.get("description"))
        price_hourly = str(request.form.get("price_hourly"))
        price_hourly = price_hourly.replace(",", ".")
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

        monday = get_or_create_open_hours(
            "Monday",
            str(request.form.get("monday_start")),
            str(request.form.get("monday_end")),
        )
        tuesday = get_or_create_open_hours(
            "Tuesday",
            str(request.form.get("tuesday_start")),
            str(request.form.get("tuesday_end")),
        )
        wednesday = get_or_create_open_hours(
            "Wednesday",
            str(request.form.get("wednesday_start")),
            str(request.form.get("wednesday_end")),
        )
        thursday = get_or_create_open_hours(
            "Thursday",
            str(request.form.get("thursday_start")),
            str(request.form.get("thursday_end")),
        )
        friday = get_or_create_open_hours(
            "Friday",
            str(request.form.get("friday_start")),
            str(request.form.get("friday_end")),
        )
        saturday = get_or_create_open_hours(
            "Saturday",
            str(request.form.get("saturday_start")),
            str(request.form.get("saturday_end")),
        )
        sunday = get_or_create_open_hours(
            "Sunday",
            str(request.form.get("sunday_start")),
            str(request.form.get("sunday_end")),
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
                    "ids_open_hours": [
                        monday,
                        tuesday,
                        wednesday,
                        thursday,
                        friday,
                        saturday,
                        sunday,
                    ],
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


@app.route("/delete_facility", methods=["POST"], admin=True, redirect_url="/")
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
        raise exc.UniqueConstraintViolated("Couldn't delete the facility")

    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)

    return redirect(url_for("index"))


# endregion FACILITY


# region MY ACCOUNT


@app.route("/my_account", methods=["GET"], logged_in=True, redirect_url="/")
def my_account_site():
    try:
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.ME,
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template(
        "my_account.html", data=data, curr_date=date.today()
    )


@app.route(
    "/edit_account_info", methods=["PUT"], logged_in=True, redirect_url="/"
)
def edit_account_info():
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
            raise exc.UniqueConstraintViolated(
                "Couldn't edit user info. Try again."
            )

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


@app.route(
    "/reset_password", methods=["GET"], logged_in=True, redirect_url="/login"
)
def reset_password_site():
    return render_template("reset_password.html")


@app.route(
    "/reset_password", methods=["PUT"], logged_in=True, redirect_url="/login"
)
def reset_password():
    try:
        old_password = str(request.form.get("old_password"))
        API.get_token(user_data()["user_data"]["email"], old_password)
        new_password = str(request.form.get("new_password"))
        repeat_password = str(request.form.get("repeat_password"))
        if repeat_password != new_password:
            raise exc.UniqueConstraintViolated("Passwords don't match.")
        try:
            API.make_request(
                API.METHOD.PUT,
                API.DATA_ENDPOINT.ME,
                query_params={
                    "password": new_password,
                },
            )
        except API.APIError as e:
            LOGGER.error(traceback.format_exc())
            return make_response(jsonify({"response": "API_ERROR"}), 405)

    except exc.UniqueConstraintViolated as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    except NoResultFound as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 404)
    except API.APIError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(
            jsonify({"response": "Incorrect old password inputted."}), 500
        )
    except ValueError as e:
        LOGGER.error(traceback.format_exc())
        return make_response(jsonify({"response": str(e)}), 500)
    return make_response(
        jsonify({"response": "Successfully changed your password."}), 200
    )


# endregion RESETTING PASSWORD

# region ADMIN PANEL


@app.route("/admin_panel", methods=["GET"], admin=True, redirect_url="/")
def admin_panel_site():
    return render_template("admin_panel.html")


# region EDIT SITE


@app.route("/edit_site", methods=["GET"], admin=True, redirect_url="/")
def edit_site_site():
    return render_template("edit_site.html")


@app.route("/edit_site", methods=["POST"], admin=True, redirect_url="/")
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
            LOGGER.error("Couldn't edit site info. Try again.")
            raise exc.UniqueConstraintViolated(
                "Couldn't edit site info. Try again."
            )

        if "file" not in request.files or not request.files['file'].filename:
            LOGGER.info("No images passed.")
            return make_response(jsonify({"response": "success, logo wasn't changed."}), 200)
        
        try:
            file = request.files["file"]
            images_handler.upload_logo(file)

        except images_handler.ImageHandlerError as e:
            LOGGER.error("Error uploading image: " + str(e))
            LOGGER.error(traceback.format_exc())
            return make_response(jsonify({"response": str(e)}), 500)


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


# endregion EDIT SITE

# endregion ADMIN PANEL


# region RESERVATIONS


@app.route("/reserve", methods=["GET"], logged_in=True, redirect_url="/")
def reserve_site():
    try:
        id_facility = int(request.args.get("id_facility"))
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.FACILITY,
            query_params={"id_facility": id_facility},
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template("reserve.html", data=data, data2=[])


@app.route(
    "/check_reservations_on_date",
    methods=["POST"],
    logged_in=True,
    redirect_url="/",
)
def check_reservations_on_date():
    try:
        id_facility = int(request.form.get("id_facility"))
        reservation_date = str(request.form.get("reservation_date"))
        if not reservation_date:
            return make_response(
                jsonify({"response": "Please input a date to check."}), 500
            )
        reserved_list = API.make_request(
            API.METHOD.GET,
            API.ACTION_ENDPOINT.RESERVED_FACILITY_HOURS,
            query_params={
                "id_facility": id_facility,
                "date": reservation_date,
            },
        )
        if not reserved_list:
            raise NoResultFound("No reservations on this day")

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
    return make_response(jsonify(reservation_list=reserved_list), 200)


@app.route("/reserve", methods=["POST"], logged_in=True, redirect_url="/")
def reserve():
    try:
        id_facility = int(request.form.get("id_facility"))
        start_time = str(request.form.get("reservation_start_time"))
        end_time = str(request.form.get("reservation_end_time"))
        reservation_date = str(request.form.get("reservation_date"))
        reservation_datetime = datetime.strptime(
            reservation_date, "%Y-%m-%d"
        ).date()
        start_hour = start_time.split(":", 1)
        end_hour = end_time.split(":", 1)
        today = date.today()
        date_in2weeks = date.today() + timedelta(days=14)
        if (
            today > reservation_datetime
            or reservation_datetime > date_in2weeks
        ):
            raise ValueError("Wrong time interval inputted.")
        if (
            start_hour[1] != end_hour[1]
        ):  # make sure the minute part of the hours are the same.
            raise ValueError("Wrong time interval inputted.")
        if (
            start_hour[0] >= end_hour[0]
        ):  # make sure the hour part of start is lower than the end time.
            raise ValueError("Wrong time interval inputted.")
        if start_hour[1] == "30" or start_hour[1] == "00":
            try:
                if not API.make_request(
                    API.METHOD.GET,
                    API.ACTION_ENDPOINT.CHECK_AVAILABILITY,
                    query_params={
                        "id_facility": id_facility,
                        "date": reservation_date,
                        "start_hour": start_time,
                        "end_hour": end_time,
                    },
                )["result"]:
                    raise ValueError("The date is unavailable.")
                API.make_request(
                    API.METHOD.GET,
                    API.ACTION_ENDPOINT.RESERVE,
                    query_params={
                        "id_facility": id_facility,
                        "id_user": user_data()["user_data"]["id_user"],
                        "date": reservation_date,
                        "start_hour": start_time,
                        "end_hour": end_time,
                    },
                )
            except API.APIError as e:
                raise API.APIError("API ERROR")
        else:
            raise ValueError("Wrong time interval inputted.")
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
    email_data={
        "title": "Facility Booking - We have confirmed your reservation",
        "body": "The details of your reservation:<br><br>Reservation date: " + reservation_date + "<br>Start hour: " + start_time + "<br>End time: " + end_time
    }
    email_handler.send_notification(email_data)
    return make_response(jsonify({"response": "success"}), 200)


@app.route("/curr_reservations", methods=["GET"], admin=True, redirect_url="/")
def curr_reservations():
    try:
        data = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.RESERVATION,
        )
    except API.APIError as e:
        LOGGER.error(e)
        data = []
    return render_template(
        "curr_reservations.html", data=data, curr_date=date.today()
    )


@app.route(
    "/delete_reservation_admin", 
    methods=["POST"], 
    admin=True, 
    redirect_url="/"
)
def delete_reservation():
    id_reservation = int(request.form.get("id_reservation"))
    try:
        API.make_request(
            API.METHOD.DELETE,
            API.DATA_ENDPOINT.RESERVATION,
            query_params={"reservation_id": id_reservation},
        )
    except API.APIError as e:
        LOGGER.info(e)
        raise exc.UniqueConstraintViolated("Couldn't delete the reservation")

    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)
    email_data={
        "title": "Facility Booking - We have cancelled your reservation",
        "body": "Your reservation has been cancelled. <br><br>Please check your reservation site for more details",
    }
    email_handler.send_notification(email_data)
    return redirect(url_for("curr_reservations"))


@app.route("/delete_reservation_me",methods=["POST"],logged_in=True,redirect_url="/",)
def delete_reservation_me():
    id_reservation = int(request.form.get("id_reservation"))
    try:
        API.make_request(
            API.METHOD.DELETE,
            API.DATA_ENDPOINT.DELETE_RESERVATION_ME,
            query_params={"reservation_id": id_reservation},
        )
    except API.APIError as e:
        LOGGER.info(e)
        raise exc.UniqueConstraintViolated("Couldn't cancel the reservation")

    except exc.UniqueConstraintViolated as e:
        return make_response(jsonify({"response": str(e)}), 500)
    email_data={
        "title": "Facility Booking - Reservation cancellation request confirmed",
        "body": "By your request, the reservation has been cancelled.<br><br>Please check your reservation site for more details",
    }
    email_handler.send_notification(email_data)
    return redirect(url_for("curr_reservations"))


# endregion RESERVATIONS


# region ACTIONS


def get_or_create_address(city_name, state_name, street_name, building_no, postal_code):
    try:
        API.make_request(
            API.METHOD.POST, API.DATA_ENDPOINT.CITY, body={"name": city_name}
        )
        API.make_request(
            API.METHOD.POST, API.DATA_ENDPOINT.STATE, body={"name": state_name}
        )
    except API.APIError as e:
        LOGGER.info(str(e))

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
        LOGGER.info("Address already exists")

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

    return address


def get_or_create_open_hours(day_name, start_hour2, end_hour2):
    start_hour2 = start_hour2[:5]
    end_hour2 = end_hour2[:5]
    start_hour = start_hour2.split(":", 1)
    end_hour = end_hour2.split(":", 1)

    if start_hour[1] != end_hour[1]:
        raise ValueError("Wrong time interval inputted.")
    if start_hour[0] >= end_hour[0]:
        raise ValueError("Wrong time interval inputted.")
    if start_hour[1] == "30" or start_hour[1] == "00":
        try:
            API.make_request(
                API.METHOD.POST,
                API.DATA_ENDPOINT.OPEN_HOUR,
                body={
                    "day_name": day_name,
                    "start_hour": start_hour2,
                    "end_hour": end_hour2,
                },
            )
        except API.APIError as e:
            LOGGER.info("Hours already exists")

        open_hours = API.make_request(
            API.METHOD.GET,
            API.DATA_ENDPOINT.OPEN_HOUR,
            query_params={
                "day_name": day_name,
                "start_hour": start_hour2,
                "end_hour": end_hour2,
            },
        )
        if not open_hours:
            raise ValueError("Inappropriate Hours")


    return open_hours[0]["id_open_hours"]


@app.template_filter("string_to_datetime")
def string_to_datetime(value):
    return datetime.strptime(value, "%Y-%m-%d").date() - timedelta(days=1)


# endregion ACTIONS


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9000)
