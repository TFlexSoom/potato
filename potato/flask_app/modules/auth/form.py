"""
module: auth
filename: form.py
date: 10/1/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines some of the models, types, and constants associated
  with login forms
"""

from dataclasses import dataclass
from typing import NewType

Uuid = NewType('Uuid', str)

@dataclass
class User:
    uuid: Uuid
    username: str
    password: str

@dataclass
class LoginForm:
    action: str
    username: str
    password: str

DEBUG_USER = LoginForm(
    "login",
    "debug_user",
    "debug",
)

PASSWORD_PLACEHOLDER = "require_no_password"
