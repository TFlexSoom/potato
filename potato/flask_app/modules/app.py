"""
filename: app.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines Verbosity and Root Settings for Flask App
"""

from dataclasses import dataclass
import logging
from typing import Any
from potato.flask_app.modules.persistance.database import db_persistance_layer
from potato.flask_app.modules.persistance.filesystem import fs_persistance_layer
from potato.server_utils.cache_utils import singleton
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

@config
@dataclass
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
def __get_module():
    return Module(
        configuration=__get_configuration(),
        start=lambda: None,
        cleanup=lambda: None
    )

@singleton
def __get_configuration():
    return FlaskConfig()

def set_logging_verbosity(logger):
    if __get_configuration().verbose:
        logger.setLevel(logging.DEBUG)
        return
    
    if __get_configuration().very_verbose:
        logger.setLevel(logging.NOTSET)
        return
    
    if __get_configuration().silent:
        logger.setLevel(logging.INFO)
        return
    
    logger.setLevel(logging.WARNING)

def get_port():
    return __get_configuration().port

def is_very_verbose():
    return __get_configuration().very_verbose

# At my last company something like this was available, but we
#   ended up putting it in its own module. Good here for now.
def get_persistance_layer():
    if __get_configuration().use_database:
        return db_persistance_layer()
    
    if __get_configuration.use_filesystem:
        return fs_persistance_layer()
    
    raise RuntimeError("No Persistance Layer!!!")