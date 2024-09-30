def start():
        config = get_config()
    project_dir = os.getcwd() #get the current working dir as the default project_dir
    config_file = None
    # if the .yaml config file is given, directly use it
    if args.config_file[-5:] == '.yaml':
        if os.path.exists(args.config_file):
            print("INFO: when you run the server directly from a .yaml file, please make sure your config file is put in the annotation project folder")
            config_file = args.config_file
            path_sep = os.path.sep
            split_path = os.path.abspath(config_file).split(path_sep)
            if split_path[-2] == "configs":
                project_dir = path_sep.join(split_path[:-2])
            else:
                project_dir = path_sep.join(split_path[:-1])
            print("project folder set as %s"%project_dir)
        else:
            print("%s not found, please make sure the .yaml config file is setup correctly" % args.config_file)
            quit()
            
    # if the user gives a directory, check if config.yaml or configs/config.yaml exists
    elif os.path.isdir(args.config_file):
        project_dir = args.config_file if os.path.isabs(args.config_file) else os.path.join(project_dir, args.config_file)
        config_folder = os.path.join(args.config_file, 'configs')
        if not os.path.isdir(config_folder):
            print(".yaml file must be put in the configs/ folder under the main project directory when you try to start the project with the project directory, otherwise please directly give the path of the .yaml file")
            quit()

        #get all the config files
        yamlfiles = [it for it in os.listdir(config_folder) if it[-5:] == '.yaml']

        # if no yaml files found, quit the program
        if len(yamlfiles) == 0:
            print("configuration file not found under %s, please make sure .yaml file exists in the given directory, or please directly give the path of the .yaml file" % config_folder)
            quit()
        # if only one yaml file found, directly use it
        elif len(yamlfiles) == 1:
            config_file = os.path.join(config_folder, yamlfiles[0])

        # if multiple yaml files found, ask the user to choose which one to use
        else:
            while True:
                print("multiple config files found, please select the one you want to use (number 0-%d)"%len(yamlfiles))
                for i,it in enumerate(yamlfiles):
                    print("[%d] %s"%(i, it))
                input_id = input("number: ")
                try:
                    config_file = os.path.join(config_folder, yamlfiles[int(input_id)])
                    break
                except Exception:
                    print("wrong input, please reselect")

    if not config_file:
        print("configuration file not found under %s, please make sure .yaml file exists in the given directory, or please directly give the path of the .yaml file" % config_folder)
        quit()

    print("starting server from %s" % config_file)
    with open(config_file, "r") as file_p:
        config.update(yaml.safe_load(file_p))

    config.update(
        {
            "verbose": args.verbose,
            "very_verbose": args.very_verbose,
            "__debug__": args.debug,
            "__config_file__": args.config_file,
        }
    )

    # update the current working dir for the server
    os.chdir(project_dir)
    print("the current working directory is: %s"%project_dir)

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

def get_displayed_text(text):
    # automatically unfold the text list when input text is a list (e.g. best-worst-scaling).
    if "list_as_text" in config and config["list_as_text"]:
        if isinstance(text, str):
            try:
                text = eval(text)
            except Exception:
                text = str(text)
        if isinstance(text, list):
            if config["list_as_text"]["text_list_prefix_type"] == "alphabet":
                prefix_list = list(string.ascii_uppercase)
                text = [prefix_list[i] + ". " + text[i] for i in range(len(text))]
            elif config["list_as_text"]["text_list_prefix_type"] == "number":
                text = [str(i) + ". " + text[i] for i in range(len(text))]
            text = "<br>".join(text)

        # unfolding dict into different sections
        elif isinstance(text, dict):
            #randomize the order of the displayed text
            if "randomization" in config["list_as_text"]:
                if config["list_as_text"].get("randomization") == "value":
                    values = list(text.values())
                    random.shuffle(values)
                    text = {key: value for key, value in zip(text.keys(), values)}
                elif config["list_as_text"].get("randomization") == "key":
                    keys = list(text.keys())
                    random.shuffle(keys)
                    text = {key: text[key] for key in keys}
                else:
                    print("WARNING: %s currently not supported for list_as_text, please check your .yaml file"%config["list_as_text"].get("randomization"))

            block = []
            if config["list_as_text"].get("horizontal"):
                for key in text:
                    block.append(
                        '<div name="instance_text" style="float:left;width:%s;padding:5px;" class="column"> <legend> %s </legend> %s </div>'
                        % ("%d" % int(100 / len(text)) + "%", key, text[key])
                    )
                text = '<div class="row" style="display: table"> %s </div>' % ("".join(block))
            else:
                for key in text:
                    block.append(
                        '<div name="instance_text"> <legend> %s </legend> %s <br/> </div>'
                        % (key, text[key])
                    )
                text = "".join(block)
        else:
            text = text
    return text
