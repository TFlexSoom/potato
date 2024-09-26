
def convert_labels(annotation, schema_type):
    if schema_type == "likert":
        return int(list(annotation.keys())[0][6:])
    if schema_type == "radio":
        return list(annotation.keys())[0]
    if schema_type == "multiselect":
        return list(annotation.keys())
    if schema_type == 'number':
        return float(annotation['text_box'])
    if schema_type == 'textbox':
        return annotation['text_box']
    print("Unrecognized schema_type %s" % schema_type)
    return None


def get_agreement_score(user_list, schema_name, return_type="overall_average"):
    """
    Get the final agreement score for selected users and schemas.
    """
    global user_to_annotation_state

    if user_list == "all":
        user_list = user_to_annotation_state.keys()

    name2alpha = {}
    if schema_name == "all":
        for i in range(len(config["annotation_schemes"])):
            schema = config["annotation_schemes"][i]
            alpha = cal_agreement(user_list, schema["name"])
            name2alpha[schema["name"]] = alpha

    alpha_list = []
    if return_type == "overall_average":
        for name in name2alpha:
            alpha = name2alpha[name]
            if isinstance(alpha, dict):
                average_alpha = sum([it[1] for it in list(alpha.items())]) / len(alpha)
                alpha_list.append(average_alpha)
            elif isinstance(alpha, (np.floating, float)):
                alpha_list.append(alpha)
            else:
                continue
        if len(alpha_list) > 0:
            return round(sum(alpha_list) / len(alpha_list), 2)
        return "N/A"

    return name2alpha


def cal_agreement(user_list, schema_name, schema_type=None, selected_keys=None):
    """
    Calculate the krippendorff's alpha for selected users and schema.
    """
    global user_to_annotation_state

    # get the schema_type/annotation_type from the config file
    for i in range(len(config["annotation_schemes"])):
        schema = config["annotation_schemes"][i]
        if schema["name"] == schema_name:
            schema_type = schema["annotation_type"]
            break

    # obtain the list of keys for calculating IAA and the user annotations
    union_keys = set()
    user_annotation_list = []
    for user in user_list:
        if user not in user_to_annotation_state:
            print("%s not found in user_to_annotation_state" % user)
        user_annotated_ids = user_to_annotation_state[user].instance_id_to_labeling.keys()
        union_keys = union_keys | user_annotated_ids
        user_annotation_list.append(user_to_annotation_state[user].instance_id_to_labeling)

    if len(user_annotation_list) < 2:
        print("Cannot calculate agreement score for less than 2 users")
        return None

    # only calculate the agreement for selected keys when selected_keys is specified
    if selected_keys is None:
        selected_keys = list(union_keys)

    if len(selected_keys) == 0:
        print(
            "Cannot calculate agreement score when annotators work on different sets of instances"
        )
        return None

    if schema_type in ["radio", "likert"]:
        distance_metric_dict = {"radio": nominal_metric, "likert": interval_metric}
        # initialize agreement data matrix
        l = []
        for _ in range(len(user_annotation_list)):
            l.append([np.nan] * len(selected_keys))

        for i, _selected_key in enumerate(selected_keys):
            for j in range(len(l)):
                if _selected_key in user_annotation_list[j]:
                    l[j][i] = convert_labels(
                        user_annotation_list[j][_selected_key][schema_name], schema_type
                    )
        alpha = simpledorff.calculate_krippendorffs_alpha(pd.DataFrame(np.array(l)),metric_fn=distance_metric_dict[schema_type])

        return alpha

    # When multiple labels are annotated for each instance, calculate the IAA for each label
    if schema_type == "multiselect":
        # collect the label list from configuration file
        if isinstance(schema["labels"][0], dict):
            labels = [it["name"] for it in schema["labels"]]
        elif isinstance(schema["labels"][0], str):
            labels = schema["labels"]
        else:
            print("Unknown label type in schema['labels']")
            return None

        # initialize agreement data matrix for each label
        l_dict = {}
        for l in labels:
            l_dict[l] = []
            for i in range(len(user_annotation_list)):
                l_dict[l].append([np.nan] * len(selected_keys))

        # consider binary agreement for each label in the multi-label schema
        for i, _selected_key in enumerate(selected_keys):
            for j in range(len(user_annotation_list)):
                if (_selected_key in user_annotation_list[j]) and (
                    schema_name in user_annotation_list[j][_selected_key]
                ):
                    annotations = convert_labels(
                        user_annotation_list[j][_selected_key][schema_name], schema_type
                    )
                    for l in labels:
                        l_dict[l][j][i] = 1
                        if l not in annotations:
                            l_dict[l][j][i] = 0

        alpha_dict = {}
        for key in labels:
            alpha_dict[key] = simpledorff.calculate_krippendorffs_alpha(pd.DataFrame(np.array(l_dict[key])),metric_fn=nominal_metric)
        return alpha_dict


def cal_amount(user):
    count = 0
    lines = user_dict[user]["user_data"]
    for key in lines:
        if lines[key]["annotated"]:
            count += 1
    return count
