"""
filename: static.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defined routes for static file serving
"""

import os
from flask import Blueprint
from server_utils.cache import singleton

@singleton
def get_blueprint():
    return Blueprint('static', __name__, static_folder=os.getcwd())