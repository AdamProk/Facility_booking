from flask import Flask, session, make_response, jsonify, redirect, url_for
from functools import wraps
from components import api_requests as API
import logging

import os

PREFIX = os.environ["PREFIX"] if os.environ.get("PREFIX") else ""
LOGGER = logging.getLogger(__name__)


class PrefixMiddleware(object):
    def __init__(self, app, prefix=""):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"].startswith(self.prefix):
            environ["PATH_INFO"] = environ["PATH_INFO"][len(self.prefix) :]
            environ["SCRIPT_NAME"] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response("404", [("Content-Type", "text/plain")])
            return ["This url does not belong to the app.".encode()]


def get_flask_app():
    app = Flask(__name__)
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=PREFIX)
    original_route = app.route

    def custom_route(
        *args, logged_in=False, admin=False, redirect_url="/login", **kwargs
    ):
        def decorator(f):
            @wraps(f)
            def wrapped_function(*function_args, **function_kwargs):
                if admin:
                    API.make_request(API.METHOD.GET,API.DATA_ENDPOINT.ME)
                    try:
                        # No admin priveledges: redirect
                        if (
                            session.get("token") is None
                            or app.user_data()["user_data"]["user_role"][
                                "name"
                            ]
                            != "Admin"
                        ):
                            return redirect(redirect_url)
                    except Exception as e:
                        LOGGER.error("Something went wrong with checking user's admin privileges. Error:"+ str(e))
                        return redirect(redirect_url)

                elif logged_in:
                    try:
                        # Not logged in: redirect
                        if session.get("token") is None:
                            return redirect(redirect_url)
                        API.make_request(API.METHOD.GET,API.DATA_ENDPOINT.ME)
                    except Exception as e:
                        LOGGER.error("Something went wrong with checking user's logged in status. Error:"+ str(e))
                        return redirect(redirect_url)

                return f(*function_args, **function_kwargs)

            return original_route(*args, **kwargs)(wrapped_function)

        return decorator

    app.route = custom_route

    return app
