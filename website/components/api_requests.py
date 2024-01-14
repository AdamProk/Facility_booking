import json
import requests
import os
from enum import Enum, auto
from flask import session, request

ON_SERVER = bool(os.environ.get("ON_SERVER"))
API_URL = "http://api:8000/" if ON_SERVER else "http://localhost:8000/"


class APIError(Exception):
    pass


class METHOD(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    GET = auto()
    POST = auto()
    PUT = auto()
    DELETE = auto()


class DATA_ENDPOINT(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    ME = auto()
    TOKEN = auto()
    USER_ROLE = auto()
    USER = auto()
    RESERVATION_STATUS = auto()
    FACILITY_TYPE = auto()
    CITY = auto()
    STATE = auto()
    ADDRESS = auto()
    DAY = auto()
    OPEN_HOUR = auto()
    COMPANY = auto()
    IMAGE = auto()
    FACILITY = auto()
    RESERVATION = auto()


class ACTION_ENDPOINT(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return "action/" + name.lower()

    CHECK_AVAILABILITY = auto()
    RESERVE = auto()
    CHECK_IF_EMAIL_EXISTS = auto()


class REQUEST_FORMAT(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return "action/" + name.lower()

    JSON = auto()
    URL_ENDCODED = auto()


def make_request(
    method: METHOD,
    endpoint: DATA_ENDPOINT | ACTION_ENDPOINT,
    query_params: dict = {},
    body: dict = {},
    headers={},
    request_format: REQUEST_FORMAT = REQUEST_FORMAT.JSON,
    token: str = None,
    get_token_from_session=True,
):
    if get_token_from_session:
        if not session.get("token"):
            raise APIError("No token in the session.")
        token = session.get("token")

    try:
        if not headers:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        if token:
            headers["Authorization"] = "Bearer " + token

        response = getattr(requests, method.value)(
            API_URL + endpoint.value,
            params=query_params,
            data=json.dumps(body)
            if request_format == REQUEST_FORMAT.JSON
            else body,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as e:
        raise APIError("Failed to connect with the API.")
    except requests.exceptions.RequestException as e:
        raise APIError(
            "{} {}: {}. DETAIL: {}".format(
                method.value, endpoint.value, str(e), response.text
            )
        )


def get_token(email: str, password: str):
    data = {
        "grant_type": "",
        "username": str(email),
        "password": str(password),
        "scope": "",
        "client_id": "",
        "client_secret": "",
    }

    response = make_request(
        METHOD.POST,
        DATA_ENDPOINT.TOKEN,
        body=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "application/x-www-form-urlencoded",
        },
        request_format=REQUEST_FORMAT.URL_ENDCODED,
        get_token_from_session=False,
    )

    token = response.get("access_token")
    if response is None or not token:
        raise APIError("Request for token unsuccessful.")

    return token
