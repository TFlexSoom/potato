"""
filename: login.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defined routes for the base page upon visiting the domain
"""

from functools import cache
import logging
from flask import Blueprint, render_template, request
from potato.flask_app.modules.auth.module import is_logged_in
from potato.flask_app.modules.prolific.module import is_using_prolific, login_prolific
from flask_app.blueprints.annotate import annotate_home
from server_utils.flask_utils import route

_logger = logging.getLogger("IndexBlueprint")

@cache
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
            _logger.log(f"could not login to prolific {e}")
            return render_template(
                "error.html",
                error_message="Please login to annotate or you are using the wrong link",
            )


    return annotate_home()


