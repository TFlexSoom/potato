"""
filename: filesystem.py
date: 09/30/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Filesystem Module for keeping the legacy behavior of potato
"""

from dataclasses import dataclass
import logging
from json import dump as json_dump, load as json_load, loads as json_loads
from typing import Callable
from csv import reader, writer
from yaml import load as yaml_load

from potato.server_utils.persistance_utils import (
    Csv, CsvResult, Filename, Json, JsonResult, 
    PersistanceLayer, Result, SQLResult, SQLString, 
    YamlResult,
)
from potato.server_utils.cache_utils import singleton
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

@singleton
def logger():
    return logging.getLogger("DatabaseLogger")

@module_getter
def __get_module():
    return Module(
        configuration=__get_configuration(),
        persistance=start,
    )

@config
@dataclass
class FileSystemConfiguration:
    debug: bool = False
    verbose: bool = False
    use_filesystem: bool = False

@singleton
def __get_configuration():
    return FileSystemConfiguration()

@dataclass
class FileSystemState:
    is_on: bool = False

@singleton
def __get_filesystem_state():
    return FileSystemState()

def start():
    if __get_configuration().use_filesystem:
        return
    pass

@singleton
def fs_persistance_layer():
    return PersistanceLayer(
        query_object=query_object,
        query_rows=query_rows,
        query_config=query_config,
        accept_object=accept_object,
        accept_rows=accept_rows,
    )


def query_object(
    filename: Filename, 
    sql: SQLString,
    json_transformer: Callable[[JsonResult], Result],
    sql_transformer: Callable[[SQLResult], Result],
) -> Result:
    with open(filename, "r") as fp:
        try:
            value = json_load(fp)
            return json_transformer(value)
        except Exception as e:
            logger().error(f"exception saving object {e}")
            
    return None

def query_object_rows(
    filename: Filename,
    sql: SQLString,
    json_transformer: Callable[[JsonResult], Result],
    sql_transformer: Callable[[SQLResult], Result],
) -> Result:
    with open(filename, "rt") as fp:
        try:
            values = [json_loads(line.strip) for line in fp.readlines()]
            return json_transformer(values)
        except Exception as e:
            logger().error(f"exception saving object {e}")
    
    return None

def query_rows(
    filename: Filename, 
    sql: SQLString,
    csv_transformer: Callable[[CsvResult], Result],
    sql_transformer: Callable[[SQLResult], Result],
) -> Result:
    with open(filename, "r") as fp:
        try:
            values = [line for line in reader(fp)]
            return csv_transformer(values)
        except Exception as e:
            logger().error(f"exception saving object {e}")
            
    return None

def query_config(
    filename: Filename, 
    sql: SQLString,
    yaml_transformer: Callable[[YamlResult], Result],
    sql_transformer: Callable[[SQLResult], Result],
) -> Result:
    with open(filename, "r") as fp:
        try:
            values = yaml_load(fp)
            return yaml_transformer(values)
        except Exception as e:
            logger().error(f"exception saving object {e}")
            
    return None
    


def accept_object(json_val: Json, sql: SQLString):
    with open(json_val.filename, "wt") as fp:
        try:
            json_dump(json_val.values, fp)
        except Exception as e:
            logger().error(f"exception saving object {e}")
            return False
    
    return True

def accept_rows(csv_val: Csv, sql: SQLString):
    with open(csv_val.filename, "wt") as fp:
        try:
            writer(fp).writerows(csv_val.values)
        except Exception as e:
            logger().error(F"exception saving object {e}")
            return False
    
    return True