"""
filename: json_utils.py
date: 10/1/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines utilities for creating json files
"""

import json
import logging

from potato.server_utils.persistence_utils import ReadResult, WriteResult

_logger = logging.getLogger("JsonUtils")

def json_write(func):
    pass

def write_data_to_truncated_file(filename, data):
    with open(filename, "wt") as fd:
        try:
            json.dump(data, fd)
        except Exception as e:
            _logger.error(f"Issue writing json data {e}")
            return WriteResult(False, e.__repr__())
    
    return WriteResult()

def read_data_from_file(filename):
    with open(filename, "r") as fd:
        try:
            data = json.load(fd)
        except Exception as e:
            _logger.error(f"Issue writing json data {e}")
            return ReadResult(False, e.__repr__(), None)
    
    return ReadResult(False, "", data)