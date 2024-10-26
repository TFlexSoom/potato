"""
filename: module.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines a module in the context of the flask server. This allows
   different modules to keep track of their own universal resources.
   This way there is a separation of responsibility
"""

from collections.abc import Callable
from dataclasses import dataclass

@dataclass
class Module:
    persistence: Callable[[], None] = lambda: None
    start: Callable[[], None] = lambda: None
    cleanup: Callable[[], None] = lambda: None

_modules = {}

def register_module(name, service: Module):
    _modules[name] = service

def module_getter(func: Callable[[], Module], name=f"SERVICE_{len(_modules.keys())}"):
    register_module(name, func())

def _roll_through(binded_func: Callable[[Module], None], process: str):
    last_service_name = ''
    try:
      for name, service in _modules.items():
         last_service_name = name
         binded_func(service)
    except Exception as e:
      print(f"Exception raised during {process} within service {last_service_name}\n{e}")
      quit(1)

def persistence():
    _roll_through(lambda service: service.persistence(), "persistence")

def start():
    _roll_through(lambda service: service.start(), "start")

def cleanup():
    _roll_through(lambda service: service.cleanup(), "cleanup")