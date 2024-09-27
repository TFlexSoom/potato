"""
filename: login.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defined routes for the base page upon visiting the domain
"""

import logging
from flask import Blueprint, render_template, request
from flask_app.modules.auth import is_logged_in
from flask_app.modules.prolific import is_using_prolific, login_prolific
from flask_app.blueprints.annotate import annotate_home
from server_utils.cache import singleton
from server_utils.flask_utils import route

@singleton
def logger():
    return logging.getLogger("IndexBlueprint")

@singleton
def get_blueprint():
    blueprint = Blueprint('index', __name__)
    home.with_blueprint(blueprint)
    return blueprint

@route("/", methods=["GET"])
def home():
    if not is_logged_in(request):
        print("password logging in")
        return render_template("home.html", title=config["annotation_task_name"])

    if is_using_prolific():
        try:
            login_prolific(request)
        except Exception as e:
            logger().log(f"could not login to prolific {e}")
            return render_template(
                "error.html",
                error_message="Please login to annotate or you are using the wrong link",
            )


    return annotate_home()


