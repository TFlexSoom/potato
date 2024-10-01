"""
filename: database.py
date: 09/30/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Database Module for making queries with mysql
"""

from dataclasses import dataclass
import logging
from typing import Callable

from potato.server_utils.persistance_utils import Csv, CsvResult, Filename, Json, JsonResult, PersistanceLayer, Result, SQLResult, SQLString, YamlResult
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
class DBConfiguration:
    debug: bool = False
    verbose: bool = False
    use_database: bool = False

@singleton
def __get_configuration():
    return DBConfiguration()

@dataclass
class DBState:
    is_on: bool = False

@singleton
def __get_db_state():
    return DBState()

def start():
    if not __get_configuration().use_database:
        return
    pass

@singleton
def db_persistance_layer():
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
   run_sql(sql)
   return sql_transformer([])

def query_rows(
    filename: Filename, 
    sql: SQLString,
    csv_transformer: Callable[[CsvResult], Result],
    sql_transformer: Callable[[SQLResult], Result],
) -> Result:
   run_sql(sql)
   return sql_transformer([])

def query_config(
    filename: Filename, 
    sql: SQLString,
    yaml_transformer: Callable[[YamlResult], Result],
    sql_transformer: Callable[[SQLResult], Result],
) -> Result:
   run_sql(sql)
   return sql_transformer([])

def accept_object(json_val: Json, sql: SQLString):
    return run_sql(sql)

def accept_rows(csv_val: Csv, sql: SQLString):
    return run_sql(sql)

def run_sql(sql: SQLString):
    logger().info(f"run sql: {sql}")
    return True