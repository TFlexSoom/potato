"""
Config module.
"""

from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, fields
from server_utils.cache import singleton

@dataclass
class __Config:
    global_config: dict[str, Any] = {}
    assertion: dict[str, Callable] = {}

@singleton
def __get_config():
    return __Config()

def __create_type_assertion(type: type):
    def __type_assertion(val):
        assert isinstance(val, type)
    
    return __type_assertion

def config(cls):
    for field in fields(cls):
        if field in __get_config().global_config:
            # could be worth logging
            continue

        assertion = __create_type_assertion(field.type)
        assertion(field.default)
        __get_config().global_config[field.name] = field.default
        __get_config().global_config[field.name] = assertion

def pull_values(obj):
    for field in fields(obj):
        setattr(obj, field.name, __get_config().global_config[field.name])
        
def from_cli_args(args):
    for key, value in vars(args):
        if key not in __get_config().global_config.keys():
            raise KeyError(f"args has {key} which is not supported by any service")

        __get_config().assertion[key](value)
        __get_config().global_config = value

def get_value(key: str):
    return __get_config().global_config[key]