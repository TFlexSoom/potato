"""
filename: login.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines Auth Service for Potato Application
"""

from dataclasses import dataclass
import logging

from server_utils.cache import singleton
from server_utils.config import config
from server_utils.module import Module, module_getter

__logger = logging.getLogger("AuthLogger")

@module_getter
def __get_module():
    return Module(
        configuration=__get_configuration(),
        start=lambda: None,
        cleanup=lambda: None
    )

@config
@dataclass
class AuthConfiguration:
    debug: bool = False,
    url_direct: bool = False,
    login_type: str = ""
    verbose: bool = False,

@singleton
def __get_configuration():
    return AuthConfiguration()

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

def clean_login_input(form: LoginForm):
    if __get_configuration().debug:
        return __DEBUG_USER
    
    if __get_configuration().login_type == "url_direct":
        form.password = __PASSWORD_PLACEHOLDER
    
    return form

def is_valid_login(form: LoginForm):
    if __get_configuration().debug:
        return True

    if __get_configuration().url_direct and form.password == __PASSWORD_PLACEHOLDER:
        return True
    
    if is_valid_password(form.username, form.password):
        return True
    
    return False

def is_valid_username(username):
    """
    Check if a user name is in the current user list.
    """
    return username in self.users

# TODO: Currently we are just doing simple plaintext verification,
# but we will need ciphertext verification in the long run
def is_valid_password(username, password):
    """
    Check if the password is correct for a given (username, password) pair.
    """
    return self.is_valid_username(username) and self.users[username]["password"] == password

def add_user(form: LoginForm) -> str:
    result = user_config.add_single_user(form)
    
    if __get_configuration().verbose:
        __logger.log(f"{form.username} {result}")
    
    return result