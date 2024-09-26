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
from server_utils.cache import singleton
from server_utils.config import Config

@dataclass
class Service:
    prestart: Callable[[], None]
    configure: function[[Config], None]
    start: Callable[[], None]
    cleanup: Callable[[], None]

@singleton
def get_services():
    return {}

def register_module(name, service: Service):
    get_services()[name] = service

def module_getter(func: Callable[[], Service], name=f"SERVICE_{len(get_services())}"):
    register_module(name, func())

def __roll_through(binded_func: Callable[[Service], None], process: str):
    last_service_name = ''
    try:
      for name, service in get_services().items():
         last_service_name = name
         binded_func(service)
    except Exception as e:
      print(f"Exception raised during {process} within service {last_service_name}\n{e}")
      quit(1)

def prestart():
    __roll_through(lambda service: service.prestart(), "prestart")

def configure(config: Config):
    __roll_through(lambda service: service.configure(config), "configure")

def start():
    __roll_through(lambda service: service.start(), "start")

def cleanup():
    __roll_through(lambda service: service.cleanup(), "cleanup")