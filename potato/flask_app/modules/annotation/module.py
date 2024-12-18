"""
module: annotation
filename: module.py
date: 09/26/2024
author: David Jurgens and Jiaxin Pei (aka Pedro)
desc: Defines annotations and the surrounded data created from user
   responses
"""

from collections import defaultdict
import logging
from random import Random
import re
import simpledorff
import pandas as pd

from potato.flask_app.modules.annotation.color import get_color_for_schema_label
from potato.flask_app.modules.prescreen.module import check_prestudy_status
from potato.flask_app.modules.project.task import assign_instances_to_user
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("Annotation")
_random = Random()
_init_tag_regex = re.compile(r"(<span.+?>)")
_end_tag_regex = re.compile(r"(</span>)")
_anno_regex = re.compile(r'<div class="span_label".+?>(.+)</div>')
_re_to_highlights = defaultdict(list)

@module_getter
def _get_module():
    return Module(
        configuration=AnnotationConfiguration,
        start=start
    )

@config
class AnnotationConfiguration:
    debug: bool = False
    output_annotation_dir: str = ""
    output_annotation_format: str = ""
    annotation_schemes: list[str] = ""

def start():
    if AnnotationConfiguration.debug:
        _random.seed(0)
    else:
        _random.seed()

def map_user_id_to_digit(user_id_str):
    # Convert the user_id_str to an integer using a hash function
    user_id_hash = hash(user_id_str)

    # Map the hashed value to a single-digit integer using modulus
    digit = abs(user_id_hash) % 9 + 1  # Add 1 to avoid 0

    return digit


def randomize_options(soup, legend_names, seed: int):
    random = Random()
    random.seed(seed)

    # Find all fieldsets in the soup
    fieldsets = soup.find_all('fieldset')
    if not fieldsets:
        _logger.debug("No fieldsets found.")
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


def parse_html_span_annotation(html_span_annotation):
    """
    Parses the span annotations produced in raw HTML by Potato's front end
    and extracts out the precise spans and labels annotated by users.

    :returns: a tuple of (1) the annotated string without annotation HTML
              and a list of annotations
    """
    s = html_span_annotation.strip()
    no_html_s = ""
    start = 0

    annotations = []

    while True:
        m = _init_tag_regex.search(s, start)
        if not m:
            break

        # find the end tag
        m2 = _end_tag_regex.search(s, m.end())

        middle = s[m.end() : m2.start()]

        # Get the annotation label from the middle text
        m3 = _anno_regex.search(middle)

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
    _random.shuffle(all_words)

    all_schemas = list([x[0] for x in _re_to_highlights.values()])

    # Grab the highlights
    for regex, labels in _re_to_highlights.items():

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
    num_false_labels = _random.randint(0, 1)

    for i in range(min(num_false_labels, len(all_words))):

        # Pick a random word
        to_highlight = all_words[i]

        # Pick a random schema and label
        schema, label = _random.choice(all_schemas)
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


def update_annotation_state(username, form, instance_id: int):
    """
    Parses the state of the HTML form (what the user did to the instance) and
    updates the state of the instance's annotations accordingly.
    """

    # Get what the user has already annotated, which might include this instance too
    user_state = lookup_user_state(username)

    # Jiaxin: the instance_id are changed to the user's local instance cursor
    instance_id = user_state.cursor_to_real_instance_id(instance_id)

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
            _logger.debug(check_prestudy_status(username))

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
    output_annotation_dir = AnnotationConfiguration.output_annotation_dir
    fmt = AnnotationConfiguration.output_annotation_format

    if fmt not in ["csv", "tsv", "json", "jsonl"]:
        raise Exception("Unsupported output format: " + fmt)

    if not os.path.exists(output_annotation_dir):
        os.makedirs(output_annotation_dir)
        _logger.debug("Created state directory for annotations: %s" % (output_annotation_dir))

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

    schemes = AnnotationConfiguration.annotation_schemes
    name2alpha = {}
    if schema_name == "all":
        for i in range(len(schemes)):
            schema = schemes[i]
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
    schemes = AnnotationConfiguration.annotation_schemes
    for i in range(len(schemes)):
        schema = schemes[i]
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
