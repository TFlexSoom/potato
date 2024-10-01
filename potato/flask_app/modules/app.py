"""
filename: app.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines Verbosity and Root Settings for Flask App
"""

import logging
from typing import Any
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

@config
class FlaskConfig:
    port: int = 8000
    silent: bool = False
    verbose: bool = False
    very_verbose: bool = False
    use_database: bool = False
    use_filesystem: bool = False

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "port":
            assert value >= 0 and value <= 65535

@module_getter
def _get_module():
    return Module(
        configuration=FlaskConfig,
        start=lambda: None,
        cleanup=lambda: None
    )

def set_logging_verbosity(logger):
    if FlaskConfig.verbose:
        logger.setLevel(logging.DEBUG)
        return
    
    if FlaskConfig.very_verbose:
        logger.setLevel(logging.NOTSET)
        return
    
    if FlaskConfig.silent:
        logger.setLevel(logging.INFO)
        return
    
    logger.setLevel(logging.WARNING)

def get_port():
    return FlaskConfig.port

def is_very_verbose():
    return FlaskConfig.very_verbose