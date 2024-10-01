"""
filename: static.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defined routes for static file serving
"""

from functools import cache
import os
from flask import Blueprint

@cache
def get_blueprint():
    return Blueprint('static', __name__, static_folder=os.getcwd())