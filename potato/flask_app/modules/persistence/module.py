"""
module: persistence
filename: module.py
date: 09/30/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Persistence module for cacheing to files, SQL databasing
  and everything to do with persisting data passed the termination
  of the program.
"""

from functools import reduce
import logging

from potato.flask_app.modules.persistence.job import _FulfillType, _PersistenceStep, _PersistenceJob
from potato.flask_app.modules.persistence.work import _work
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("Persistence")

@module_getter
def _get_module():
    return Module(
        configuration=PersistenceConfig,
        persistence=start
    )

@config
class PersistenceConfig:
    debug: bool = False
    verbose: bool = False
    use_embedded: bool = False
    use_database: bool = False
    use_filesystem: bool = False

def start():
    pass

def persist(job_steps: list[_PersistenceStep]):
    job = reduce(lambda step, job: step.transform(job), job_steps, _PersistenceJob())
    return _perform(job)

def _perform(job: _PersistenceJob):
    if len(job.fulfill_with) == 0:
        raise RuntimeError("Nothing to fulfill job with")

    allowed = {
        _FulfillType.Csv : PersistenceConfig.use_filesystem,
        _FulfillType.Json : PersistenceConfig.use_filesystem,
        _FulfillType.Yaml : PersistenceConfig.use_filesystem,
        _FulfillType.SQLite : PersistenceConfig.use_embedded,
        _FulfillType.MySQL : PersistenceConfig.use_database,
    }

    fulfilled = False
    result = None
    for fulfillment in job.fulfill_with:
        if not allowed[fulfillment]:
            continue

        fulfilled = True

        # TODO how to combine all results from all jobs
        result = _work(fulfillment, job)

    if not fulfilled:
        raise RuntimeError("Could not persist due to unsupported fulfillment")

    return result


    

