"""
module: sampling
filename: module.py
date: 09/26/2024
author: David Jurgens
desc: Defines Sampling for Annotators to keep questions randomized
"""

import logging
import os
import os.path
import json
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("SamplingLogger")

@module_getter
def __get_module():
    return Module(
        configuration=SamplingConfiguration,
    )

@config
class SamplingConfiguration:
    debug: bool = False

def sample_instances(username):
    global user_to_annotation_state
    global instance_id_to_data

    # check if sampling strategy is specified in configuration, if not, set it as random
    if "sampling_strategy" not in config["automatic_assignment"] \
           or config["automatic_assignment"]["sampling_strategy"] not in ['random','ordered']:
        _logger.debug("Undefined sampling strategy, default to random assignment")
        config["automatic_assignment"]["sampling_strategy"] = "random"

    # Force the sampling strategy to be random at this moment, will change this
    # when more sampling strategies are created
    #config["automatic_assignment"]["sampling_strategy"] = "random"

    if config["automatic_assignment"]["sampling_strategy"] == "random":
        # previously we were doing random sample directly, however, when there
        # are a large amount of instances and users, it is possible that some
        # instances are rarely sampled and some are oversampled at the end of
        # the sampling process
        # sampled_keys = random.sample(list(task_assignment['unassigned'].keys()),
        #                             config["automatic_assignment"]["instance_per_annotator"])

        # Currently we will shuffle the unassinged keys first, and then rank
        # the dict based on the availability of each instance, and they directly
        # get the first N instances
        unassigned_dict = task_assignment["unassigned"]
        unassigned_dict = {
            k: unassigned_dict[k]
            for k in random.sample(list(unassigned_dict.keys()), len(unassigned_dict))
        }
        sorted_keys = [
            it[0] for it in sorted(unassigned_dict.items(), key=lambda item: item[1], reverse=True)
        ]
        sampled_keys = sorted_keys[
            : min(config["automatic_assignment"]["instance_per_annotator"], len(sorted_keys))
        ]

    elif config["automatic_assignment"]["sampling_strategy"] == "ordered":
        # sampling instances based on the natural order of the data

        sorted_keys = list(task_assignment["unassigned"].keys())
        sampled_keys = sorted_keys[
                       : min(config["automatic_assignment"]["instance_per_annotator"], len(sorted_keys))
        ]
        #print(sampled_keys)

    # update task_assignment to keep track of task assignment status globally
    for key in sampled_keys:
        if key not in task_assignment["assigned"]:
            task_assignment["assigned"][key] = []
        task_assignment["assigned"][key].append(username)
        task_assignment["unassigned"][key] -= 1
        if task_assignment["unassigned"][key] == 0:
            del task_assignment["unassigned"][key]

    # sample and insert test questions
    if task_assignment["testing"]["test_question_per_annotator"] > 0:
        sampled_testing_ids = random.sample(
            task_assignment["testing"]["ids"],
            k=task_assignment["testing"]["test_question_per_annotator"],
        )
        # adding test question sampling status to the task assignment
        for key in sampled_testing_ids:
            if key not in task_assignment["assigned"]:
                task_assignment["assigned"][key] = []
            task_assignment["assigned"][key].append(username)
            sampled_keys.insert(random.randint(0, len(sampled_keys) - 1), key)

    return sampled_keys

def generate_initial_user_dataflow(username):
    """
    Generate initial dataflow for a new annotator including surveyflows and prestudy.
    :return: UserAnnotationState
    """
    global user_to_annotation_state
    global instance_id_to_data

    sampled_keys = []
    for it in ["pre_annotation_pages", "prestudy_ids"]:
        if it in task_assignment:
            sampled_keys += task_assignment[it]

    assigned_user_data = {key: instance_id_to_data[key] for key in sampled_keys}

    # save the assigned user data dict
    user_dir = os.path.join(config["output_annotation_dir"], username)
    assigned_user_data_path = os.path.join(user_dir, "assigned_user_data.json")

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        _logger.debug('Created state directory for user "%s"' % (username))

    with open(assigned_user_data_path, "w") as w:
        json.dump(assigned_user_data, w)

    # return the assigned user data dict
    return assigned_user_data


def generate_full_user_dataflow(username):
    """
    Directly assign all the instances to a user at the beginning of the study
    :return: UserAnnotationState
    """
    global user_to_annotation_state
    global instance_id_to_data

    #check if sampling strategy is specified in configuration, if not, set it as random
    if "sampling_strategy" not in config["automatic_assignment"] or config["automatic_assignment"]["sampling_strategy"] not in ['random','ordered']:
        _logger.debug("Undefined sampling strategy, default to random assignment")
        config["automatic_assignment"]["sampling_strategy"] = "random"

    # Force the sampling strategy to be random at this moment, will change this
    # when more sampling strategies are created
    #config["automatic_assignment"]["sampling_strategy"] = "random"

    if config["automatic_assignment"]["sampling_strategy"] == "random":
        sampled_keys = random.sample(
            list(task_assignment["unassigned"].keys()),
            config["automatic_assignment"]["instance_per_annotator"],
        )
    elif config["automatic_assignment"]["sampling_strategy"] == "ordered":
        # sampling instances based on the natural order of the data

        sorted_keys = list(task_assignment["unassigned"].keys())
        sampled_keys = sorted_keys[
                       : min(config["automatic_assignment"]["instance_per_annotator"], len(sorted_keys))
                       ]

    # update task_assignment to keep track of task assignment status globally
    for key in sampled_keys:
        if key not in task_assignment["assigned"]:
            task_assignment["assigned"][key] = []
        task_assignment["assigned"][key].append(username)
        task_assignment["unassigned"][key] -= 1
        if task_assignment["unassigned"][key] == 0:
            del task_assignment["unassigned"][key]

    # sample and insert test questions
    if task_assignment["testing"]["test_question_per_annotator"] > 0:
        sampled_testing_ids = random.sample(
            task_assignment["testing"]["ids"],
            k=task_assignment["testing"]["test_question_per_annotator"],
        )
        # adding test question sampling status to the task assignment
        for key in sampled_testing_ids:
            if key not in task_assignment["assigned"]:
                task_assignment["assigned"][key] = []
            task_assignment["assigned"][key].append(username)
            sampled_keys.insert(random.randint(0, len(sampled_keys) - 1), key)

    # save task assignment status
    task_assignment_path = os.path.join(
        config["output_annotation_dir"], config["automatic_assignment"]["output_filename"]
    )
    with open(task_assignment_path, "w") as w:
        json.dump(task_assignment, w)

    # add the amount of sampled instances
    real_assigned_instance_count = len(sampled_keys)

    if "pre_annotation_pages" in task_assignment:
        sampled_keys = task_assignment["pre_annotation_pages"] + sampled_keys

    if "post_annotation_pages" in task_assignment:
        sampled_keys = sampled_keys + task_assignment["post_annotation_pages"]

    assigned_user_data = {key: instance_id_to_data[key] for key in sampled_keys}

    # save the assigned user data dict
    user_dir = os.path.join(config["output_annotation_dir"], username)
    assigned_user_data_path = os.path.join(user_dir, "assigned_user_data.json")

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        _logger.debug('Created state directory for user "%s"' % (username))

    with open(assigned_user_data_path, "w") as w:
        json.dump(assigned_user_data, w)

    # return the assigned user data dict
    return assigned_user_data, real_assigned_instance_count
