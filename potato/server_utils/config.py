"""
Config module.
"""

import yaml
import os

from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
from server_utils.cache import singleton

@dataclass
class ConfigListItem:
    item_name: str
    item_type: type
    item_default: Any

@dataclass
class __Config:
    global_config: dict[str, Any] = {}
    assertion: dict[str, Callable] = {}

    # config_list: ConfigListItem
    # verbose: bool = False
    # very_verbose: bool = False
    # debug: bool = False
    # prolific: dict = {}
    # login: dict = { "type": "" }
    # user_config_file: str = "user_config.json"
    # project_config_file: str = ""
    # output_annotation_dir: str = ""

@singleton
def __get_config():
    return __Config()

def __create_type_assertion(type: type):
    def __type_assertion(val):
        assert isinstance(val, type)
    
    return __type_assertion

def add_config(definition: list[ConfigListItem]):
    for definition_item in definition:
        assertion = __create_type_assertion(definition_item.item_type)
        assertion(definition_item.item_default)
        __get_config().global_config[definition_item.name] = definition_item.item_default
        __get_config().global_config[definition_item.name] = assertion

def from_cli_args(args):
    for key, value in vars(args):
        if key not in __get_config().global_config.keys():
            raise KeyError(f"args has {key} which is not supported by any service")

        __get_config().assertion[key](value)
        __get_config().global_config = value

def get_value(key: str):
    return __get_config().global_config[key]