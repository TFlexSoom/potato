"""
module: auth
filename: module.py
date: 09/26/2024
author: Jiaxin Pei (aka Pedro) and Tristan Hilbert (aka TFlexSoom)
desc: Defines Auth Service for Potato Application
"""

import logging

from potato.flask_app.modules.auth.form import DEBUG_USER, PASSWORD_PLACEHOLDER, LoginForm, User, Uuid
from potato.flask_app.modules.persistence.filesystem import fs_persistence_layer
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("AuthLogger")
_allow_all_users: bool = False

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
    allow_all_users: bool = False


def start():
    global _allow_all_users
    if AuthConfiguration.allow_all_users:
        _allow_all_users = True

    if not AuthConfiguration.is_loading_users:
        return
    
    user_config_path = AuthConfiguration.user_config_path
    if not os.path.isfile(user_config_path):
        return
    
    _logger.info(f"Loading users from {user_config_path}")
    users = fs_persistence_layer().query_object_rows(
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
        return DEBUG_USER
    
    if AuthConfiguration.login_type == "url_direct":
        form.password = PASSWORD_PLACEHOLDER
    
    return form

def is_valid_login(form: LoginForm, args):
    if AuthConfiguration.debug:
        return True
    
    if _allow_all_users:
        return True

    if AuthConfiguration.login_type == "url_direct":
        url_arguments = AuthConfiguration.login_argument
        username = '&'.join([args.get(it) for it in url_arguments])
        _logger.info(f"url direct logging in with {'&'.join(url_arguments)}={username}")
        return True
    
    if AuthConfiguration.url_direct and form.password == PASSWORD_PLACEHOLDER:
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