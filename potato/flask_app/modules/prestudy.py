
def get_prestudy_label(label):
    for schema in config["annotation_schemes"]:
        if schema["name"] == config["prestudy"]["question_key"]:
            cur_schema = schema["annotation_type"]
    label = convert_labels(label[config["prestudy"]["question_key"]], cur_schema)
    return config["prestudy"]["answer_mapping"][label] if "answer_mapping" in config["prestudy"] else label


def print_prestudy_result():
    global task_assignment
    print("----- prestudy test result -----")
    print("passed annotators: ", task_assignment["prestudy_passed_users"])
    print("failed annotators: ", task_assignment["prestudy_failed_users"])
    print(
        "pass rate: ",
        len(task_assignment["prestudy_passed_users"])
        / len(task_assignment["prestudy_passed_users"] + task_assignment["prestudy_failed_users"]),
    )


def check_prestudy_status(username):
    """
    Check whether a user has passed the prestudy test (this function will only be used )
    :return:
    """
    global task_assignment
    global instance_id_to_data

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

    print_prestudy_result()

    # update the annotation list according the prestudy test result
    assign_instances_to_user(username)

    return prestudy_result