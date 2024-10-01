"""
filename: login.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines Auth Service for Potato Application
"""

from dataclasses import dataclass
import logging
import os
from typing import NewType

from potato.flask_app.modules.filesystem.filesystem import fs_persistance_layer
from potato.server_utils.cache_utils import singleton
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

@singleton
def logger():
    return logging.getLogger("AuthLogger")

@module_getter
def _get_module():
    return Module(
        configuration=AuthConfiguration,
        start=start
    )

@config
class AuthConfiguration:
    debug: bool = False
    url_direct: bool = False
    login_type: str = ""
    login_argument: str = "username"
    is_loading_users: bool = True
    user_config_path: str = "potato/user_config.json"
    verbose: bool = False
    use_database: bool = False

@dataclass
class LoginForm:
    action: str
    username: str
    password: str

__DEBUG_USER = LoginForm(
    "login",
    "debug_user",
    "debug",
)

__PASSWORD_PLACEHOLDER = "require_no_password"

Uuid = NewType('Uuid', str)

@dataclass
class User:
    uuid: Uuid
    username: str
    password: str

@dataclass
class AuthState:
    allow_all_users: bool = True
    users: dict[Uuid, User]
    username_lookup: dict[str, Uuid]

@singleton
def __get_auth_state():
    return AuthState()

def start():
    if not AuthConfiguration.is_loading_users:
        return
    
    user_config_path = AuthConfiguration.user_config_path
    if not os.path.isfile(user_config_path):
        return
    
    logger().info(f"Loading users from {user_config_path}")
    users = fs_persistance_layer().query_object_rows(
        user_config_path,
        "", # For SQL stick to db
        lambda user_json_list: user_json_list,
        lambda result : None,
    )

    for user in users:
        from_json_to_cached_user(user)


def from_json_to_cached_user(user: dict):
    uuid = user.get('uuid', 'uuid') # TODO fix
    username = user.get('username', 'unknown') # TODO fix

    assert not uuid in __get_auth_state().users
    assert not username in __get_auth_state().username_lookup

    __get_auth_state().users[user.uuid] = User(
        uuid,
        username,
        user.get('password', 'password'), # TODO Fix
    )

    __get_auth_state().username_lookup[username] = uuid


def clean_login_input(form: LoginForm):
    if AuthConfiguration.debug:
        return __DEBUG_USER
    
    if AuthConfiguration.login_type == "url_direct":
        form.password = __PASSWORD_PLACEHOLDER
    
    return form

def is_valid_login(form: LoginForm, args):
    if AuthConfiguration.debug:
        return True
    
    if __get_auth_state().allow_all_users:
        return True

    if AuthConfiguration.login_type == "url_direct":
        url_arguments = AuthConfiguration.login_argument
        username = '&'.join([args.get(it) for it in url_arguments])
        logger().info(f"url direct logging in with {'&'.join(url_arguments)}={username}")
        return True
    
    if AuthConfiguration.url_direct and form.password == __PASSWORD_PLACEHOLDER:
        return True
    
    if is_valid_password(form.username, form.password):
        return True
    
    return False

def username_exists(username):
    """
    Check if a user name is in the current user list.
    """
    return username in __get_auth_state().username_lookup

def is_valid_password(username, password):
    """
    Check if the password is correct for a given (username, password) pair.
    """
    uuid = __get_auth_state().username_lookup.get(username)
    if uuid == None:
        return False

    # TODO Fix
    return __get_auth_state().users[uuid].password == password

def add_user(form: LoginForm) -> bool:
    username = form.username
    if username_exists(username):
        return False

    uuid = "", # generate uuid TODO fix

    __get_auth_state().users[uuid] = User(
        uuid,
        username,
        form.password, # TODO Fix
    )

    __get_auth_state().username_lookup[username] = uuid
    
    return True