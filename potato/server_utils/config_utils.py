"""
filename: module.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines a configuration which allows all of the modules
  to request a series of entries within the configuration (this
  comes from the cli-args, .env, and other sources) such that
  there is a single source of truth for 'configuration'
"""

from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, fields

@dataclass
class _GlobalConfig:
    values: dict[str, Any] = {}
    assertion: dict[str, Callable] = {}

_global_config = _GlobalConfig()

def _create_type_assertion(type: type):
    def _type_assertion(val):
        assert isinstance(val, type)
    
    return _type_assertion

class Config:
    def __getattr__(self, name: str) -> Any:
        return _global_config().values[name]
    
    def __setattr__(self, name: str, value: Any) -> None:
        raise Exception("Configs are Immutable")

def config(cls, *args, **kwargs):
    cls = dataclass(args, kwargs)

    for field in fields(cls):
        if field in _global_config().values:
            # could be worth logging
            continue

        assertion = _create_type_assertion(field.type)
        assertion(field.default)
        _global_config().values[field.name] = field.default
        _global_config().values[field.name] = assertion
    
    return Config()
        
def from_cli_args(args):
    for key, value in vars(args):
        if key not in _global_config().values.keys():
            raise KeyError(f"args has {key} which is not supported by any service")

        _global_config().assertion[key](value)
        _global_config().values = value

def get_value(key: str):
    return _global_config().values[key]