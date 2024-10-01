"""
module: persistance
filename: module.py
date: 09/30/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Persistance module for cacheing to files, SQL databasing
  and everything to do with persisting data passed the termination
  of the program.
"""

import logging

from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("Persistance")

@module_getter
def _get_module():
    return Module(
        configuration=PersistanceConfig,
    )

@config
class PersistanceConfig:
    pass