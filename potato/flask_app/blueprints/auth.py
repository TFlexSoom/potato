"""
filename: login.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defined routes for login/logout and other authentication
   needs
"""

from functools import cache
from flask import Blueprint, render_template, request
from potato.flask_app.modules.auth.module import (
    LoginForm, clean_login_input, is_valid_login, add_user
)
from server_utils.flask_utils import route

@cache
def get_blueprint():
    blueprint = Blueprint('auth', __name__)
    login.with_blueprint(blueprint)
    signup.with_blueprint(blueprint)
    return blueprint

@route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(
        request.form.get("action"),
        request.form.get("email"),
        request.form.get("password")
    )

    form = clean_login_input(form)

    # TODO Modify Cookies with token
    # user_config.is_valid_password(username, password)

    if form.action != "login":
        print("unknown action at home page")
        return render_template("home.html", title=config["annotation_task_name"])
    
    if is_valid_login(form):
        # if surveyflow is setup, jump to the page before annotation
        print("%s login successful" % form.username)
        return annotate_page(form.username)
    
    return render_template(
        "home.html",
        title=config["annotation_task_name"],
        login_email=form.username,
        login_error="Invalid username or password",
    )


@route("/signup", methods=["GET", "POST"])
def signup():
    form = LoginForm(
        request.form.get("action"),
        request.form.get("email"),
        request.form.get("password")
    )

    if form.action != "signup":
        print("unknown action at home page")
        return render_template(
            "home.html",
            title=config["annotation_task_name"],
            login_email=form.username,
            login_error="Invalid username or password",
        )

    result = add_user(form)

    if result == "Success":
        return render_template(
            "home.html",
            title=config["annotation_task_name"],
            login_email=form.username,
            login_error="User registration success for " + form.username + ", please login now",
        )
    elif result == 'Unauthorized user':
        return render_template(
            "home.html",
            title=config["annotation_task_name"],
            login_error=result + ", please contact your admin",
        )

    else: 
        return render_template(
            "home.html",
            title=config["annotation_task_name"],
            login_error=result + ", please try again or log in",
        )

    
