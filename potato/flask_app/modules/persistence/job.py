"""
module: persistence
filename: job.py
date: 09/30/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Types and utilities for interfacing with the persistence
  layer so that file and sql transactions are easier
"""

from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Any, Callable, Optional, Type

from potato.server_utils.persistence import ReadResult

_persistent_sources = {}

@dataclass
class Persistence:
    data_name: str
    key_type: Type
    filename: Optional[str]

# called during script-load rather than during runtime
def designate_persistence(cls: Type, key_cls: Type, filename: Optional[str] = None):
    _persistent_sources[cls.__name__] = Persistence(
        data_name = cls.__name__,
        key_type = key_cls,
        filename = filename,
    )

def set_filename(cls: Type, filename: str):
    _persistent_sources[cls.__name__].filename = filename

class _FulfillType(Enum):
    Csv = 1
    Json = 2
    Yaml = 3
    SQLite = 4
    MySQL = 5

@dataclass
class _PersistenceJob:
    fulfill_with: list[_FulfillType] = []
    filename: Optional[str] = None
    query: Optional[str] = None
    read_mapper: Optional[Callable[[ReadResult], Any]] = None
    write_mapper: Optional[Callable[[Any], Any]] = None
    values: Optional[Any] = None
    is_exist_check: bool = False

@dataclass
class _PersistenceStep:
    transform: Callable[[_PersistenceJob], _PersistenceJob]

