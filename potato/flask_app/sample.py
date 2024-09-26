
def sample_instances(username):
    global user_to_annotation_state
    global instance_id_to_data

    # check if sampling strategy is specified in configuration, if not, set it as random
    if "sampling_strategy" not in config["automatic_assignment"] \
           or config["automatic_assignment"]["sampling_strategy"] not in ['random','ordered']:
        logger.debug("Undefined sampling strategy, default to random assignment")
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