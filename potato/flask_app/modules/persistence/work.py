"""
module: persistence
filename: work.py
date: 10/01/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Working the persistence jobs provided by the persistence module
"""

from os.path import exists
from dataclasses import dataclass
from json import load as json_load, dump as json_dump
from csv import reader as csv_reader, writer as csv_writer
from yaml import load as yaml_load, dump as yaml_dump
import logging
from typing import Any, Callable
from potato.flask_app.modules.persistence.job import _FulfillType, _PersistenceJob

_logger = logging.getLogger("PersistenceWork")

def _log_work(job: _PersistenceJob):
    _logger.info(
        f"Types: {job.fulfill_with}"
        f"\nFilename: {job.filename}" +
        f"\nQuery: {job.query}" + 
        f"\nread_mapper: {job.read_mapper.__name__ if job.read_mapper != None else None}"
        f"\nwrite_mapper: {job.write_mapper.__name__ if job.write_mapper != None else None}"
        f"\nvalues: {job.values}"
        f"\nexists_check: {job.is_exist_check}"
    )

def _work(type: _FulfillType, job: _PersistenceJob):
    if job.is_exist_check:
        return _fulfillments[type].exists(job)
    elif job.read_mapper == None:
        return _fulfillments[type].writer(job)
    else:
        return _fulfillments[type].reader(job)

def _file_exists(job: _PersistenceJob):
    return exists(job.values)

def _load_csv(job: _PersistenceJob):
    with open(job.filename, "r") as fp:
        try:
            values = [line for line in csv_reader(fp)]
            return job.read_mapper(values)
        except Exception as e:
            _logger.error(f"exception loading object {e}")
            return None

def _write_csv(job: _PersistenceJob):
    with open(job.filename, "wt") as fp:
        try:
            values = job.write_mapper(job.values)
            csv_writer(fp).writerows(values)
        except Exception as e:
            _logger.error(F"exception saving object {e}")
            return False
    
    return True

def _load_json(job: _PersistenceJob):
    with open(job.filename, "r") as fp:
        try:
            value = json_load(fp)
            return job.read_mapper(value)
        except Exception as e:
            _logger.error(f"exception loading object {e}")
            return None

def _write_json(job: _PersistenceJob):
    with open(job.filename, "wt") as fp:
        try:
            values = job.write_mapper(job.values)
            json_dump(values, fp)
        except Exception as e:
            _logger.error(F"exception saving object {e}")
            return False
    
    return True

def _load_yaml(job: _PersistenceJob):
    with open(job.filename, "r") as fp:
        try:
            value = yaml_load(fp)
            return job.read_mapper(value)
        except Exception as e:
            _logger.error(f"exception loading object {e}")
            
    return None

def _write_yaml(job: _PersistenceJob):
    with open(job.filename, "wt") as fp:
        try:
            values = job.write_mapper(job.values)
            yaml_dump(values, fp)
        except Exception as e:
            _logger.error(f"exception saving object {e}")
            return False
        
    return True

def _exists_sqlite(job: _PersistenceJob):
    try:
        pass
    except Exception as e:
        _logger.error(f"exception checking object {e}")
        return False

def _load_sqlite(job: _PersistenceJob):
    try:
        pass
    except Exception as e:
        _logger.error(f"exception loading object {e}")

def _write_sqlite(job: _PersistenceJob):
    try:
        pass
    except Exception as e:
        _logger.error(f"exception saving object {e}")

def _exists_mysql(job: _PersistenceJob):
    try:
        pass
    except Exception as e:
        _logger.error(f"exception checking object {e}")
        return False

def _load_mysql(job: _PersistenceJob):
    try:
        pass
    except Exception as e:
        _logger.error(f"exception loading object {e}")


def _write_mysql(job: _PersistenceJob):
    try:
        pass
    except Exception as e:
        _logger.error(f"exception saving object {e}")


@dataclass
class _WorkFulfillment:
    exists: Callable[[_PersistenceJob], bool]
    reader: Callable[[_PersistenceJob], Any]
    writer: Callable[[_PersistenceJob], Any] 

_fulfillments = {
    _FulfillType.Csv: _WorkFulfillment(_file_exists, _load_csv, _write_csv),
    _FulfillType.Json:  _WorkFulfillment(_file_exists, _load_json, _write_json),
    _FulfillType.Yaml: _WorkFulfillment(_file_exists, _load_yaml, _write_yaml),
    _FulfillType.SQLite:  _WorkFulfillment(_exists_sqlite, _load_sqlite, _write_sqlite),
    _FulfillType.MySQL:  _WorkFulfillment(_exists_mysql, _load_mysql, _write_mysql),
}
