"""
filename: persistance_utils.py
date: 10/1/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines utilities for writing data to persistant
  volumes and containers
"""

from dataclasses import dataclass
from typing import Any

@dataclass
class WriteResult:
    success: bool = True
    msg: str = ""

@dataclass
class ReadResult:
    success: bool = True
    msg: str = ""
    value: Any = None


