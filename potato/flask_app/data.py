def load_all_data(config):
    global instance_id_to_data
    global task_assignment

    # Hacky nonsense
    global re_to_highlights

    # Where to look in the JSON item object for the text to annotate
    text_key = config["item_properties"]["text_key"]
    id_key = config["item_properties"]["id_key"]

    # Keep the data in the same order we read it in
    instance_id_to_data = OrderedDict()

    data_files = config["data_files"]
    logger.debug("Loading data from %d files" % (len(data_files)))

    for data_fname in data_files:

        fmt = data_fname.split(".")[-1]
        if fmt not in ["csv", "tsv", "json", "jsonl"]:
            raise Exception("Unsupported input file format %s for %s" % (fmt, data_fname))

        logger.debug("Reading data from " + data_fname)

        if fmt in ["json", "jsonl"]:
            with open(data_fname, "rt") as f:
                for line_no, line in enumerate(f):
                    item = json.loads(line)

                    # fix the encoding
                    # item[text_key] = item[text_key].encode("latin-1").decode("utf-8")

                    instance_id = item[id_key]

                    # TODO: check for duplicate instance_id
                    instance_id_to_data[instance_id] = item

        else:
            sep = "," if fmt == "csv" else "\t"
            # Ensure the key is loaded as a string form (prevents weirdness
            # later)
            df = pd.read_csv(data_fname, sep=sep, dtype={id_key: str, text_key: str})
            for _, row in df.iterrows():

                item = {}
                for c in df.columns:
                    item[c] = row[c]
                instance_id = row[id_key]

                # TODO: check for duplicate instance_id
                instance_id_to_data[instance_id] = item
            line_no = len(df)

        logger.debug("Loaded %d instances from %s" % (line_no, data_fname))

    # TODO Setup automatic test questions for each annotation schema,
    # currently we are doing it similar to survey flow to allow multilingual test questions
    if "surveyflow" in config and config["surveyflow"]["on"]:
        for test_file in config["surveyflow"].get("testing", []):
            with open(test_file, "r") as r:
                for line in r:
                    line = json.loads(line.strip())
                    for l in line["choices"]:
                        item = {
                            "id": line["id"] + "_testing_" + l,
                            "text": line["text"].replace("[test_question_choice]", l),
                        }
                        # currently we simply move all these test questions to the end of the instance list
                        instance_id_to_data.update({item["id"]: item})
                        instance_id_to_data.move_to_end(item["id"], last=True)

    # insert survey questions into instance_id_to_data
    for page in config.get("pre_annotation_pages", []):
        # TODO Currently we simply remove the language type before -,
        # but we need a more elegant way for this in the future
        item = {"id": page['id'], "text": page['text'] if 'text' in page else page['id'].split("-")[-1][:-5]}
        instance_id_to_data.update({page['id']: item})
        instance_id_to_data.move_to_end(page['id'], last=False)

    for it in ["prestudy_failed_pages", "prestudy_passed_pages"]:
        for page in config.get(it, []):
            # TODO Currently we simply remove the language type before -,
            # but we need a more elegant way for this in the future
            item = {"id": page['id'], "text": page['text'] if 'text' in page else page['id'].split("-")[-1][:-5]}
            instance_id_to_data.update({page['id']: item})
            instance_id_to_data.move_to_end(page['id'], last=False)

    for page in config.get("post_annotation_pages", []):
        item = {"id": page['id'], "text": page['text'] if 'text' in page else page['id'].split("-")[-1][:-5]}
        instance_id_to_data.update({page['id']: item})
        instance_id_to_data.move_to_end(page['id'], last=True)

    # Generate the text to display in instance_id_to_data
    for inst_id in instance_id_to_data:
        instance_id_to_data[inst_id]["displayed_text"] = get_displayed_text(
            instance_id_to_data[inst_id][config["item_properties"]["text_key"]]
        )

    # TODO: make this fully configurable somehow...
    re_to_highlights = defaultdict(list)
    if "keyword_highlights_file" in config:
        kh_file = config["keyword_highlights_file"]
        logger.debug("Loading keyword highlighting from %s" % (kh_file))

        with open(kh_file, "rt") as f:
            # TODO: make it flexible based on keyword
            df = pd.read_csv(kh_file, sep="\t")
            for i, row in df.iterrows():
                regex = r"\b" + row["Word"].replace("*", "[a-z]*?") + r"\b"
                re_to_highlights[regex].append((row["Schema"], row["Label"]))

        logger.debug(
            "Loaded %d regexes to map to %d labels for dynamic highlighting"
            % (len(re_to_highlights), i)
        )

    # Load the annotation assignment info if automatic task assignment is on.
    # Jiaxin: we are simply saving this as a json file at this moment
    if "automatic_assignment" in config and config["automatic_assignment"]["on"]:

        # path to save task assignment information
        task_assignment_path = os.path.join(
            config["output_annotation_dir"], config["automatic_assignment"]["output_filename"]
        )

        if os.path.exists(task_assignment_path):
            # load the task assignment if it has been generated and saved
            with open(task_assignment_path, "r") as r:
                task_assignment = json.load(r)
        else:
            # Otherwise generate a new task assignment dict
            task_assignment = {
                "assigned": {},
                "unassigned": OrderedDict(), #use ordered dict so that we can keep track of the original order
                "testing": {"test_question_per_annotator": 0, "ids": []},
                "prestudy_ids": [],
                "prestudy_passed_users": [],
                "prestudy_failed_users": [],
            }
            # Setting test_question_per_annotator if it is defined in automatic_assignment,
            # otherwise it is default to 0 and no test question will be used
            if "test_question_per_annotator" in config["automatic_assignment"]:
                task_assignment["testing"]["test_question_per_annotator"] = config[
                    "automatic_assignment"
                ]["test_question_per_annotator"]

            for it in ["pre_annotation", "prestudy_passed", "prestudy_failed", "post_annotation"]:
                if it + "_pages" in config:
                    task_assignment[it + "_pages"] = [p['id'] if type(p) == dict else p for p in config[it + "_pages"]]
                    for p in config[it + "_pages"]:
                        task_assignment["assigned"][p['id']] = 0

            for _id in instance_id_to_data:
                if _id in task_assignment["assigned"]:
                    continue
                # add test questions to the assignment dict
                if re.search("testing", _id):
                    task_assignment["testing"]["ids"].append(_id)
                    continue
                if re.search("prestudy", _id):
                    task_assignment["prestudy_ids"].append(_id)
                    continue
                # set the total labels per instance, if not specified, default to 3
                task_assignment["unassigned"][_id] = (
                    config["automatic_assignment"]["labels_per_instance"]
                    if "labels_per_instance" in config["automatic_assignment"]
                    else DEFAULT_LABELS_PER_INSTANCE
                )