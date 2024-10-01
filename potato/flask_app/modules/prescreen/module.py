"""
module: prescreen
filename: module.py
date: 09/26/2024
author: David Jurgens and Jiaxin Pei (aka Pedro)
desc: Defines the workings of the data for the prescreener,
  validating annotators fall within the correct constraints
"""

import logging
from random import Random

from potato.flask_app.modules.annotation.module import convert_labels
from potato.flask_app.modules.project.task import assign_instances_to_user
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("Prescreen")
_random = Random()

@module_getter
def _get_module():
    return Module(
        configuration=PrescreenConfiguration,
        start=start
    )

@config
class PrescreenConfiguration:
    debug: bool = False
    annotation_schemes: list[str] = ""
    prestudy_question_key: str = ""
    prestudy_answer_mapping: dict = {}

def start():
    if PrescreenConfiguration.debug:
        _random.seed(0)
    else:
        _random.seed()

def get_prestudy_label(label):
    schemes = PrescreenConfiguration.annotation_schemes
    question_key = PrescreenConfiguration.prestudy_question_key
    answer_mapping = PrescreenConfiguration.prestudy_answer_mapping
    for schema in schemes:
        if schema["name"] == question_key:
            cur_schema = schema["annotation_type"]
    label = convert_labels(label[question_key], cur_schema)
    return answer_mapping[label] if len(answer_mapping.keys()) != 0 else label


def print_prestudy_result(task_assignment):
    _logger.info("----- prestudy test result -----")
    _logger.info("passed annotators: ", task_assignment["prestudy_passed_users"])
    _logger.info("failed annotators: ", task_assignment["prestudy_failed_users"])
    _logger.info(
        "pass rate: ",
        len(task_assignment["prestudy_passed_users"])
        / len(task_assignment["prestudy_passed_users"] + task_assignment["prestudy_failed_users"]),
    )


def check_prestudy_status(username, task_assignment: dict):
    """
    Check whether a user has passed the prestudy test (this function will only be used )
    :return:
    """

    if "prestudy" not in config or config["prestudy"]["on"] is False:
        return "no prestudy test"

    user_state = lookup_user_state(username)

    # directly return the status if the user has passed/failed the prestudy before
    if user_state.get_prestudy_status() == False:
        return "prestudy failed"
    elif user_state.get_prestudy_status() == True:
        return "prestudy passed"

    res = []
    for _id in task_assignment["prestudy_ids"]:
        label = user_state.get_label_annotations(_id)
        if label is None:
            return "prestudy not complete"
        groundtruth = instance_id_to_data[_id][config["prestudy"]["groundtruth_key"]]
        label = get_prestudy_label(label)
        print(label, groundtruth)
        res.append(label == groundtruth)

    print(res, sum(res) / len(res))
    # check if the score is higher than the minimum defined in config
    if (sum(res) / len(res)) < config["prestudy"]["minimum_score"]:
        user_state.set_prestudy_status(False)
        task_assignment["prestudy_failed_users"].append(username)
        prestudy_result = "prestudy just failed"
    else:
        user_state.set_prestudy_status(True)
        task_assignment["prestudy_passed_users"].append(username)
        prestudy_result = "prestudy just passed"

    print_prestudy_result(task_assignment)

    # update the annotation list according the prestudy test result
    assign_instances_to_user(username)

    return prestudy_result