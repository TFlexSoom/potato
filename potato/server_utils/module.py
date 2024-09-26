"""
filename: module.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines a module in the context of the flask server. This allows
   different modules to keep track of their own universal resources.
   This way there is a separation of responsibility
"""

from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
from server_utils.cache import singleton
from server_utils.config import pull_values

@dataclass
class Module:
    configuration: Any
    start: Callable[[], None]
    cleanup: Callable[[], None]

@singleton
def get_modules():
    return {}

def register_module(name, service: Module):
    get_modules()[name] = service

def module_getter(func: Callable[[], Module], name=f"SERVICE_{len(get_modules())}"):
    register_module(name, func())

def __roll_through(binded_func: Callable[[Module], None], process: str):
    last_service_name = ''
    try:
      for name, service in get_modules().items():
         last_service_name = name
         binded_func(service)
    except Exception as e:
      print(f"Exception raised during {process} within service {last_service_name}\n{e}")
      quit(1)

def configure():
    __roll_through(lambda service: pull_values(service.configuration), "configure")

def start():
    __roll_through(lambda service: service.start(), "start")

def cleanup():
    __roll_through(lambda service: service.cleanup(), "cleanup")