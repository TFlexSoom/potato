COLOR_PALETTE = [
    "rgb(179,226,205)",
    "rgb(253,205,172)",
    "rgb(203,213,232)",
    "rgb(244,202,228)",
    "rgb(230,245,201)",
    "rgb(255,242,174)",
    "rgb(241,226,204)",
    "rgb(204,204,204)",
    "rgb(102, 197, 204)",
    "rgb(246, 207, 113)",
    "rgb(248, 156, 116)",
    "rgb(220, 176, 242)",
    "rgb(135, 197, 95)",
    "rgb(158, 185, 243)",
    "rgb(254, 136, 177)",
    "rgb(201, 219, 116)",
    "rgb(139, 224, 164)",
    "rgb(180, 151, 231)",
    "rgb(179, 179, 179)",
]

@app.route("/annotate", methods=["GET", "POST"])
def annotate_page(username=None, action=None):
    """
    Parses the input received from the user's annotation and takes some action
    based on what was clicked/typed. This method is the main switch for changing
    the state of the server for this user.
    """
    global user_config

    # use the provided username when the username is given
    if not username:
        if config["__debug__"]:
            username = "debug_user"
        else:
            username_from_last_page = request.form.get("email")
            if username_from_last_page is None:
                return render_template(
                    "error.html",
                    error_message="Please login to annotate or you are using the wrong link",
                )
            username = username_from_last_page

    # Check if the user is authorized. If not, go to the login page
    # if not user_config.is_valid_username(username):
    #    return render_template("home.html")

    # Based on what the user did to the instance, update the annotate state for
    # this instance. All of the instances clicks/checks/text are stored in the
    # request.form object, which has the name of the HTML element and its value.
    #
    # If the user actually changed the annotate state (as opposed to just moving
    # through instances), then save the state of the annotations.
    #
    # NOTE: I *think* this is safe from race conditions since the flask server
    # is running in a single thread, but it's probably good to check on this at
    # some point if we scale to having lots of concurrent users.
    if "instance_id" in request.form:
        did_change = update_annotation_state(username, request.form)

        if did_change:

            # Check if we need to run active learning to re-order instances. We
            # do this before saving the user state in case the order does change.o
            #
            # NOTE: In a perfect world, this would be done in a separate process
            # that is synchronized and users get their next instance from some
            # centrally managed queue so we don't block while doing all this
            # training. However, such advanced wizardry is beyond this MVP and
            # will have to wait
            if (
                "active_learning_config" in config
                and config["active_learning_config"]["enable_active_learning"]
            ):

                # Check to see if we've hit the threshold for the number of
                # annotations needed
                al_config = config["active_learning_config"]

                # How many total annotations do we need to have
                update_rate = al_config["update_rate"]
                total_annotations = get_total_annotations()

                if total_annotations % update_rate == 0:
                    actively_learn()

            save_user_state(username)

            # Save everything in a separate thread to avoid I/O issues
            th = threading.Thread(target=save_all_annotations)
            th.start()

    # AJYL: Note that action can still be None, if "src" not in request.form.
    # Not sure if this is intended.
    action = request.form.get("src") if action is None else action

    if action == "home":
        result_code = load_user_state(username)
        if result_code == "all instances have been assigned":
            return render_template(
                "error.html",
                error_message="Sorry that you come a bit late. We have collected enough responses for our study. However, prolific sometimes will recruit more participants than we expected. We are sorry for the inconvenience!",
            )

    elif action == "prev_instance":
        move_to_prev_instance(username)

    elif action == "next_instance":
        move_to_next_instance(username)

    elif action == "go_to":
        go_to_id(username, request.form.get("go_to"))

    else:
        print('unrecognized action request: "%s"' % action)

    instance = get_cur_instance_for_user(username)

    id_key = config["item_properties"]["id_key"]
    if config["annotation_task_name"] == "Contextual Acceptability":
        context_key = config["item_properties"]["context_key"]

    # directly display the prepared displayed_text
    instance_id = instance[id_key]
    text = instance["displayed_text"]

    # also save the displayed text in the metadata dict
    # instance_id_to_data[instance_id]['displayed_text'] = text

    # If the user has labeled spans within this instance before, replace the
    # current instance text with pre-annotated mark-up. We do this here before
    # the render_template call so that we can directly insert the span-marked-up
    # HTML into the template.
    #
    # NOTE: This currently requires a very tight (and kludgy) binding between
    # the UI code for how Potato represents span annotations and how the
    # back-end displays these. Future work when we are better programmers will
    # pass this info to client side for rendering, rather than doing
    # pre-rendering here. This also means that any changes to the UI code for
    # rendering need to be updated here too.
    #
    # NOTE2: We have to this here to account for any keyword highlighting before
    # the instance text gets marked up in the post-processing below
    span_annotations = get_span_annotations_for_user_on(username, instance_id)
    if span_annotations is not None and len(span_annotations) > 0:
        # Mark up the instance text where the annotated spans were
        text = render_span_annotations(text, span_annotations)

    # If the admin has specified that certain keywords need to be highlighted,
    # post-process the selected instance so that it now also has colored span
    # overlays for keywords.
    #
    # NOTE: this code is probably going to break the span annotation's
    # understanding of the instance. Need to check this...
    updated_text, schema_labels_to_highlight, schema_content_to_prefill = text, set(), []

    #prepare label suggestions
    if 'label_suggestions' in instance:
        suggestions = instance['label_suggestions']
        for scheme in config['annotation_schemes']:
            if scheme['name'] not in suggestions:
                continue
            suggested_labels = suggestions[scheme['name']]
            if type(suggested_labels) == str:
                suggested_labels = [suggested_labels]
            elif type(suggested_labels) == list:
                suggested_labels = suggested_labels
            else:
                print("WARNING: Unsupported suggested label type %s, please check your input data" % type(s))
                continue

            if scheme.get('label_suggestions') == 'highlight':
                for s in suggested_labels:
                    schema_labels_to_highlight.add((scheme['name'], s))
            elif scheme.get('label_suggestions') == 'prefill':
                for s in suggested_labels:
                    schema_content_to_prefill.append({'name':scheme['name'], 'label':s})
            else:
                print('WARNING: the style of suggested labels is not defined, please check your configuration file.')

    if "keyword_highlights_file" in config and len(schema_labels_to_highlight) == 0:
        updated_text, schema_labels_to_highlight = post_process(config, text)

    # Fill in the kwargs that the user wanted us to include when rendering the page
    kwargs = {}
    for kw in config["item_properties"].get("kwargs", []):
        if kw in instance:
            kwargs[kw] = instance[kw]

    all_statistics = lookup_user_state(username).generate_user_statistics()

    # TODO: Display plots for agreement scores instead of only the overall score
    # in the statistics sidebar
    # all_statistics['Agreement'] = get_agreement_score('all', 'all', return_type='overall_average')
    # print(all_statistics)

    # Set the html file as surveyflow pages when the instance is a not an
    # annotation page (survey pages, prestudy pass or fail page)
    if instance_id in config.get("non_annotation_pages", []):
        html_file = instance_id
    # otherwise set the page as the normal annotation page
    else:
        html_file = config["site_file"]

    # Flask will fill in the things we need into the HTML template we've created,
    # replacing {{variable_name}} with the associated text for keyword arguments
    rendered_html = render_template(
        html_file,
        username=username,
        # This is what instance the user is currently on
        instance=text,
        instance_obj=instance,
        instance_id=lookup_user_state(username).get_instance_cursor(),
        finished=lookup_user_state(username).get_real_finished_instance_count(),
        total_count=lookup_user_state(username).get_real_assigned_instance_count(),
        alert_time_each_instance=config["alert_time_each_instance"],
        statistics_nav=all_statistics,
        **kwargs
    )

    # UGHGHGHGH the template does unusual escaping, which makes it a PAIN to do
    # the replacement later
    # m = re.search('<div name="instance_text">(.*?)</div>', rendered_html,
    #              flags=(re.DOTALL|re.MULTILINE))
    # text = m.group(1)

    # For whatever reason, doing this before the render_template causes the
    # embedded HTML to get escaped, so we just do a wholesale replacement here.
    rendered_html = rendered_html.replace(text, updated_text)

    # Parse the page so we can programmatically reset the annotation state
    # to what it was before
    soup = BeautifulSoup(rendered_html, "html.parser")

    # Highlight the schema's labels as necessary
    for schema, label in schema_labels_to_highlight:

        name = schema + ":::" + label
        label_elem = soup.find("label", {"for": name})

        # Update style to match the current color
        c = get_color_for_schema_label(schema, label)

        # Jiaxin: sometimes label_elem is None
        if label_elem:
            label_elem["style"] = "background-color: %s" % c


    # If the user has annotated this before, walk the DOM and fill out what they
    # did
    annotations = get_annotations_for_user_on(username, instance_id)

    # convert the label suggestions into annotations for front-end rendering
    if annotations == None and schema_content_to_prefill:
        scheme_dict = {}
        annotations = defaultdict(dict)
        for it in config['annotation_schemes']:
            if it['annotation_type'] in ['radio', 'multiselect']:
                it['label2value'] = {(l if type(l) == str else l['name']):str(i+1) for i,l in enumerate(it['labels'])}
            scheme_dict[it['name']] = it
        for s in schema_content_to_prefill:
            if scheme_dict[s['name']]['annotation_type'] in ['radio', 'multiselect']:
                annotations[s['name']][s['label']] = scheme_dict[s['name']]['label2value'][s['label']]
            elif scheme_dict[s['name']]['annotation_type'] in ['text']:
                if "labels" not in scheme_dict[s['name']]:
                    annotations[s['name']]['text_box'] = s['label']
            else:
                print('WARNING: label suggestions not supported for annotation_type %s, please submit a github issue to get support'%scheme_dict[s['name']]['annotation_type'])
    #print(schema_content_to_prefill, annotations)


    if annotations is not None:
        # Reset the state
        for schema, labels in annotations.items():
            for label, value in labels.items():

                name = schema + ":::" + label

                # Find all the input, select, and textarea tags with this name
                # (which was annotated) and figure out which one to fill in
                input_fields = soup.find_all(["input", "select", "textarea"], {"name": name})

                for input_field in input_fields:
                    if input_field is None:
                        print("No input for ", name)
                        continue

                    # If it's a slider, set the value for the slider
                    if input_field['type'] == 'range' and name.startswith('slider:::'):
                        input_field['value'] = value
                        continue

                    # If it's not a text area, let's see if this is the button
                    # that was checked, and if so mark it as checked
                    if input_field.name != "textarea" and input_field.has_attr("value") and input_field.get("value") != value:
                        continue
                    else:
                        input_field["checked"] = True
                        input_field["value"] = value

                    # Set the input value for textarea input
                    if input_field.name == "textarea":
                        input_field.string = value

                    # Find the right option and set it as selected if the current
                    # annotation schema is a select box
                    elif label == "select-one":
                        option = input_field.findChildren("option", {"value": value})[0]
                        option["selected"] = "selected"

    # randomize the order of options for multirate schema
    selected_schemas_for_option_randomization = []
    for it in config['annotation_schemes']:
        if it['annotation_type'] == 'multirate' and it.get('option_randomization'):
            selected_schemas_for_option_randomization.append(it['description'])

    if len(selected_schemas_for_option_randomization) > 0:
        soup = randomize_options(soup, selected_schemas_for_option_randomization, map_user_id_to_digit(username))

    rendered_html = str(soup)

    return rendered_html




def map_user_id_to_digit(user_id_str):
    # Convert the user_id_str to an integer using a hash function
    user_id_hash = hash(user_id_str)

    # Map the hashed value to a single-digit integer using modulus
    digit = abs(user_id_hash) % 9 + 1  # Add 1 to avoid 0

    return digit


def randomize_options(soup, legend_names, seed):
    random.seed(seed)

    # Find all fieldsets in the soup
    fieldsets = soup.find_all('fieldset')
    if not fieldsets:
        print("No fieldsets found.")
        return soup

    # Initialize a variable to track whether the legend is found
    legend_found = False

    # Iterate through each fieldset
    for fieldset in fieldsets:
        # Find the legend within the current fieldset
        legend = fieldset.find('legend')
        if legend and legend.string in legend_names:
            # Legend found, set the flag and break the loop
            legend_found = True

            # Find the table within the fieldset
            table = fieldset.find('table')
            if not table:
                print("Table not found within the fieldset.")
                continue

            # Get the list of tr elements excluding the first one (title)
            tr_elements = table.find_all('tr')[1:]

            # Shuffle the tr elements based on the given random seed
            random.shuffle(tr_elements)

            # Insert the shuffled tr elements back into the tbody
            for tr in tr_elements:
                table.append(tr)

    # Check if any legend was found
    if not legend_found:
        print(f"No matching legends found within any fieldset.")

    return soup


def get_color_for_schema_label(schema, label):
    global schema_label_to_color

    t = (schema, label)
    if t in schema_label_to_color:
        return schema_label_to_color[t]
    c = COLOR_PALETTE[len(schema_label_to_color)]
    schema_label_to_color[t] = c
    return c


def parse_html_span_annotation(html_span_annotation):
    """
    Parses the span annotations produced in raw HTML by Potato's front end
    and extracts out the precise spans and labels annotated by users.

    :returns: a tuple of (1) the annotated string without annotation HTML
              and a list of annotations
    """
    s = html_span_annotation.strip()
    init_tag_regex = re.compile(r"(<span.+?>)")
    end_tag_regex = re.compile(r"(</span>)")
    anno_regex = re.compile(r'<div class="span_label".+?>(.+)</div>')
    no_html_s = ""
    start = 0

    annotations = []

    while True:
        m = init_tag_regex.search(s, start)
        if not m:
            break

        # find the end tag
        m2 = end_tag_regex.search(s, m.end())

        middle = s[m.end() : m2.start()]

        # Get the annotation label from the middle text
        m3 = anno_regex.search(middle)

        middle_text = middle[: m3.start()]
        annotation = m3.group(1)

        no_html_s += s[start : m.start()]

        ann = {
            "start": len(no_html_s),
            "end": len(no_html_s) + len(middle_text),
            "span": middle_text,
            "annotation": annotation,
        }
        annotations.append(ann)

        no_html_s += middle_text
        start = m2.end(0)

    # Add whatever trailing text exists
    no_html_s += s[start:]

    return no_html_s, annotations


def post_process(config, text):
    global schema_label_to_color

    schema_labels_to_highlight = set()

    all_words = list(set(re.findall(r"\b[a-z]{4,}\b", text)))
    all_words = [w for w in all_words if not w.startswith("http")]
    random.shuffle(all_words)

    all_schemas = list([x[0] for x in re_to_highlights.values()])

    # Grab the highlights
    for regex, labels in re_to_highlights.items():

        search_from = 0

        regex = re.compile(regex, re.I)

        while True:
            try:
                match = regex.search(text, search_from)
            except BaseException as e:
                print(repr(e))
                break

            if match is None:
                break

            start = match.start()
            end = match.end()

            # we're going to replace this instance with a color coded one
            if len(labels) == 1:
                schema, label = labels[0]

                schema_labels_to_highlight.add((schema, label))

                c = get_color_for_schema_label(schema, label)

                pre = '<span style="background-color: %s">' % c

                replacement = pre + match.group() + "</span>"

                text = text[:start] + replacement + text[end:]

                # Be sure to count all the junk we just added when searching again
                search_from += end + (len(replacement) - len(match.group()))

            # slightly harder, but just to get the MVP out
            elif len(labels) == 2:

                colors = []

                for schema, label in labels:
                    schema_labels_to_highlight.add((schema, label))
                    c = get_color_for_schema_label(schema, label)
                    colors.append(c)

                matched_word = match.group()

                first_half = matched_word[: int(len(matched_word) / 2)]
                last_half = matched_word[int(len(matched_word) / 2) :]

                pre = '<span style="background-color: %s;">'

                replacement = (
                    (pre % colors[0])
                    + first_half
                    + "</span>"
                    + (pre % colors[1])
                    + last_half
                    + "</span>"
                )

                text = text[:start] + replacement + text[end:]

                # Be sure to count all the junk we just added when searching again
                search_from += end + (len(replacement) - len(matched_word))

            # Gotta make this hard somehow...
            else:
                search_from = end

    # Pick a few random words to highlight
    #
    # NOTE: we do this after the label assignment because if we somehow screw up
    # and wrongly flag a valid word, this coloring is embedded within the outer
    # (correct) <span> tag, so the word will get labeled correctly
    num_false_labels = random.randint(0, 1)

    for i in range(min(num_false_labels, len(all_words))):

        # Pick a random word
        to_highlight = all_words[i]

        # Pick a random schema and label
        schema, label = random.choice(all_schemas)
        schema_labels_to_highlight.add((schema, label))

        # Figure out where this word occurs
        c = get_color_for_schema_label(schema, label)

        search_from = 0
        regex = r"\b" + to_highlight + r"\b"
        regex = re.compile(regex, re.I)

        while True:
            try:
                match = regex.search(text, search_from)
            except BaseException as e:
                print(repr(e))
                break
            if match is None:
                break

            start = match.start()
            end = match.end()

            pre = '<span style="background-color: %s">' % c

            replacement = pre + match.group() + "</span>"
            text = text[:start] + replacement + text[end:]

            # Be sure to count all the junk we just added when searching again
            search_from += end + (len(replacement) - len(match.group()))

    return text, schema_labels_to_highlight

def get_total_annotations():
    """
    Returns the total number of unique annotations done across all users.
    """
    total = 0
    for username in get_users():
        user_state = lookup_user_state(username)
        total += user_state.get_real_finished_instance_count()

    return total


def update_annotation_state(username, form):
    """
    Parses the state of the HTML form (what the user did to the instance) and
    updates the state of the instance's annotations accordingly.
    """

    # Get what the user has already annotated, which might include this instance too
    user_state = lookup_user_state(username)

    # Jiaxin: the instance_id are changed to the user's local instance cursor
    instance_id = user_state.cursor_to_real_instance_id(int(request.form["instance_id"]))

    schema_to_label_to_value = defaultdict(dict)

    behavioral_data_dict = {}

    did_change = False
    for key in form:

        # look for behavioral information regarding time, click, ...
        if key[:9] == "behavior_":
            behavioral_data_dict[key[9:]] = form[key]
            continue

        # Look for the marker that indicates an annotation label.
        #
        # NOTE: The span annotation uses radio buttons as well to figure out
        # which label. These inputs are labeled with "span_label" so we can skip
        # them as being actual annotatins (the spans are saved below though).
        if ":::" in key and "span_label" not in key:

            cols = key.split(":::")
            annotation_schema = cols[0]
            annotation_label = cols[1]
            annotation_value = form[key]

            # skip the input when it is an empty string (from a text-box)
            if annotation_value == "":
                continue

            schema_to_label_to_value[annotation_schema][annotation_label] = annotation_value


    # Span annotations are a bit funkier since we're getting raw HTML that
    # we need to post-process on the server side.
    span_annotations = []
    if "span-annotation" in form:
        span_annotation_html = form["span-annotation"]
        span_text, span_annotations = parse_html_span_annotation(span_annotation_html)

    did_change = user_state.set_annotation(
        instance_id, schema_to_label_to_value, span_annotations, behavioral_data_dict
    )

    # update the behavioral information regarding time only when the annotations are changed
    if did_change:
        user_state.instance_id_to_behavioral_data[instance_id] = behavioral_data_dict

        # todo: we probably need a more elegant way to check the status of user consent
        # when the user agreed to participate, try to assign
        if re.search("consent", instance_id):
            consent_key = "I want to participate in this research and continue with the study."
            user_state.consent_agreed = False
            if schema_to_label_to_value[consent_key].get("Yes") == "true":
                user_state.consent_agreed = True
            assign_instances_to_user(username)

        # when the user is working on prestudy, check the status
        if re.search("prestudy", instance_id):
            print(check_prestudy_status(username))

    return did_change

def get_annotations_for_user_on(username, instance_id):
    """
    Returns the label-based annotations made by this user on the instance.
    """
    user_state = lookup_user_state(username)
    annotations = user_state.get_label_annotations(instance_id)
    return annotations


def get_span_annotations_for_user_on(username, instance_id):
    """
    Returns the span annotations made by this user on the instance.
    """
    user_state = lookup_user_state(username)
    span_annotations = user_state.get_span_annotations(instance_id)
    return span_annotations

def save_all_annotations():
    global user_to_annotation_state
    global instance_id_to_data

    # Figure out where this user's data would be stored on disk
    output_annotation_dir = config["output_annotation_dir"]
    fmt = config["output_annotation_format"]

    if fmt not in ["csv", "tsv", "json", "jsonl"]:
        raise Exception("Unsupported output format: " + fmt)

    if not os.path.exists(output_annotation_dir):
        os.makedirs(output_annotation_dir)
        logger.debug("Created state directory for annotations: %s" % (output_annotation_dir))

    annotated_instances_fname = os.path.join(output_annotation_dir, "annotated_instances." + fmt)

    # We write jsonl format regardless
    if fmt in ["json", "jsonl"]:
        with open(annotated_instances_fname, "wt") as outf:
            for user_id, user_state in user_to_annotation_state.items():
                for inst_id, data in user_state.get_all_annotations().items():

                    bd_dict = user_state.instance_id_to_behavioral_data.get(inst_id, {})

                    output = {
                        "user_id": user_id,  # "user_id
                        "instance_id": inst_id,
                        "displayed_text": instance_id_to_data[inst_id]["displayed_text"],
                        "label_annotations": data["labels"],
                        "span_annotations": data["spans"],
                        "behavioral_data": bd_dict,
                    }
                    json.dump(output, outf)
                    outf.write("\n")

    # Convert to Pandas and then dump
    elif fmt in ["csv", "tsv"]:
        df = defaultdict(list)

        # Loop 1, figure out which schemas/labels have values so we know which
        # things will need to be columns in each row
        schema_to_labels = defaultdict(set)
        span_labels = set()

        for user_state in user_to_annotation_state.values():
            for annotations in user_state.get_all_annotations().values():
                # Columns for each label-based annotation
                for schema, label_vals in annotations["labels"].items():
                    for label in label_vals.keys():
                        schema_to_labels[schema].add(label)

                # Columns for each span type too
                for span in annotations["spans"]:
                    span_labels.add(span["annotation"])

                # TODO: figure out what's in the behavioral dict and how to format it

        # Loop 2, report everything that's been annotated
        for user_id, user_state in user_to_annotation_state.items():
            for inst_id, annotations in user_state.get_all_annotations().items():

                df["user"].append(user_id)
                df["instance_id"].append(inst_id)
                df["displayed_text"].append(instance_id_to_data[inst_id]["displayed_text"])

                label_annotations = annotations["labels"]
                span_annotations = annotations["spans"]

                for schema, labels in schema_to_labels.items():
                    if schema in label_annotations:
                        label_vals = label_annotations[schema]
                        for label in labels:
                            val = label_vals[label] if label in label_vals else None
                            # For some sanity, combine the schema and label it a single column
                            df[schema + ":::" + label].append(val)
                    # If the user did label this schema at all, fill it with None values
                    else:
                        for label in labels:
                            df[schema + ":::" + label].append(None)

                # We bunch spans by their label to make it slightly easier to
                # process, but it's still kind of messy compared with the JSON
                # format.
                for span_label in span_labels:
                    anns = [sa for sa in span_annotations if sa["annotation"] == span_label]
                    df["span_annotation:::" + span_label].append(anns)

                # TODO: figure out what's in the behavioral dict and how to format it

        df = pd.DataFrame(df)
        sep = "," if fmt == "csv" else "\t"
        df.to_csv(annotated_instances_fname, index=False, sep=sep)

    # Save the annotation assignment info if automatic task assignment is on.
    # Jiaxin: we are simply saving this as a json file at this moment
    if "automatic_assignment" in config and config["automatic_assignment"]["on"]:
        # TODO: write the code here
        print("saved")