"""
filename: flask_utils.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: To avoid global scope creep among other issues, these utilities
  seek to help with some of the clutter that goes along with flask
"""

from dataclasses import dataclass
from collections.abc import Callable
from flask import Blueprint

class CallableRoute:
    call: Callable[[], None]
    with_blueprint: Callable[[Blueprint], None]

def route(func, *args, **kwargs):
    def with_blueprint(blueprint):
        blueprint.route(*args, **kwargs)(func)
    
    return CallableRoute(
        call=func,
        with_blueprint=with_blueprint,
    )