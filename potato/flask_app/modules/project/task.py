"""
module: project
filename: task.py
date: 09/26/2024
author: David Jurgens and Jiaxin Pei (aka Pedro)
desc: Defines the assignment of tasks in a helper file for the
  project module
"""

import logging

_logger = logging.getLogger("Task")

def assign_instances_to_user(username):
    """
    Assign instances to a user
    :return: UserAnnotationState
    """
    global user_to_annotation_state
    global instance_id_to_data

    user_state = user_to_annotation_state[username]

    # check if the user has already been assigned with instances to annotate
    # Currently we are just assigning once, but we might chance this later
    if user_state.get_real_assigned_instance_count() > 0:
        logging.warning(
            "Instance already assigned to user %s, assigning process stoppped" % username
        )
        return False

    prestudy_status = user_state.get_prestudy_status()
    consent_status = user_state.get_consent_status()

    if prestudy_status is None:
        if "prestudy" in config and config["prestudy"]["on"]:
            logging.warning(
                "Trying to assign instances to user when the prestudy test is not completed, assigning process stoppped"
            )
            return False

        if (
            "surveyflow" not in config
            or not config["surveyflow"]["on"]
            or "prestudy" not in config
            or not config["prestudy"]["on"]
        ) or consent_status:
            sampled_keys = sample_instances(username)
            user_state.real_instance_assigned_count += len(sampled_keys)
            if "post_annotation_pages" in task_assignment:
                sampled_keys = sampled_keys + task_assignment["post_annotation_pages"]
        else:
            logging.warning(
                "Trying to assign instances to user when the user has yet agreed to participate. assigning process stoppped"
            )
            return False

    elif prestudy_status is False:
        sampled_keys = task_assignment["prestudy_failed_pages"]

    else:
        sampled_keys = sample_instances(username)
        user_state.real_instance_assigned_count += len(sampled_keys)
        sampled_keys = task_assignment["prestudy_passed_pages"] + sampled_keys
        if "post_annotation_pages" in task_assignment:
            sampled_keys = sampled_keys + task_assignment["post_annotation_pages"]

    assigned_user_data = {key: instance_id_to_data[key] for key in sampled_keys}
    user_state.add_new_assigned_data(assigned_user_data)

    print(
        "assinged %d instances to %s, total pages: %s, total users: %s, unassigned labels: %s, finished users: %s"
        % (
            user_state.get_real_assigned_instance_count(),
            username,
            user_state.get_assigned_instance_count(),
            get_total_user_count(),
            get_unassigned_count(),
            get_finished_user_count()
        )
    )

    # save the assigned user data dict
    user_dir = os.path.join(config["output_annotation_dir"], username)
    assigned_user_data_path = os.path.join(user_dir, "assigned_user_data.json")

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        _logger.debug('Created state directory for user "%s"' % (username))

    with open(assigned_user_data_path, "w") as w:
        json.dump(user_state.get_assigned_data(), w)

    # save task assignment status
    task_assignment_path = os.path.join(
        config["output_annotation_dir"], config["automatic_assignment"]["output_filename"]
    )
    with open(task_assignment_path, "w") as w:
        json.dump(task_assignment, w)

    user_state.instance_assigned = True

    # return the assigned user data dict
    return assigned_user_data


def remove_instances_from_users(user_set):
    """
    Remove users from the annotation state, move the saved annotations to another folder
    Release the assigned instances
    """
    global user_to_annotation_state
    global archived_users
    global instance_id_to_data
    global task_assignment

    if len(user_set) == 0:
        print('No users need to be dropped at this moment')
        return None

    #remove user from the global user_to_annotation_state
    for u in user_set:
        if u in user_to_annotation_state:
            archived_users = user_to_annotation_state[u]
            del user_to_annotation_state[u]

    #remove assigned instances
    for inst_id in task_assignment['assigned']:
        new_li = []
        if type(task_assignment['assigned'][inst_id]) != list:
            continue
        for u in task_assignment['assigned'][inst_id]:
            if u in user_set:
                if inst_id not in task_assignment['unassigned']:
                    task_assignment['unassigned'][inst_id] = 0
                task_assignment['unassigned'][inst_id] += 1
            else:
                new_li.append(u)
        # if len(new_li) != len(task_assignment['assigned'][inst_id]):
        #    print(task_assignment['assigned'][inst_id], new_li)
        task_assignment['assigned'][inst_id] = new_li

    # Figure out where this user's data would be stored on disk
    output_annotation_dir = config["output_annotation_dir"]

    # move the bad users into a separate dir under annotation output
    bad_user_dir = os.path.join(output_annotation_dir, "archived_users")
    if not os.path.exists(bad_user_dir):
        os.mkdir(bad_user_dir)
    for u in user_set:
        if os.path.exists(os.path.join(output_annotation_dir, u)):
            shutil.move(os.path.join(output_annotation_dir, u), os.path.join(bad_user_dir, u))
    print('bad users moved to %s' % bad_user_dir)
    print('removed %s users from the current annotation queue' % len(user_set))


def instances_all_assigned():
    global task_assignment

    if 'unassigned' in task_assignment and len(task_assignment['unassigned']) <= int(config["automatic_assignment"]["instance_per_annotator"] * 0.7):
        return True
    return False


def get_unassigned_count():
    """
    return the number of unassigned instances
    """
    global task_assignment
    if 'unassigned' in task_assignment:
        return sum(list(task_assignment['unassigned'].values()))
    else:
        return 0
