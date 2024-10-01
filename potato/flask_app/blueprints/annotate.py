"""
filename: login.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defined routes for login/logout and other authentication needs
"""

from flask import Blueprint, render_template, request
from potato.flask_app.modules.auth.auth import is_logged_in
from potato.server_utils.cache_utils import singleton
from server_utils.flask_utils import route

@singleton
def get_blueprint():
    blueprint = Blueprint('annotate', __name__)
    annotate_page.with_blueprint(blueprint)
    return blueprint

@route("/annotate-home", methods=["GET", "POST"])
def annotate_home():
    result_code = load_user_state(username)
    if result_code == "all instances have been assigned":
        return render_template(
            "error.html",
            error_message="Sorry that you come a bit late. We have collected enough responses for our study. However, prolific sometimes will recruit more participants than we expected. We are sorry for the inconvenience!",
        )

@route("/annotate-prev", methods=["GET", "POST"])
def annotate_prev():
    return annotate_paginate(False)

@route("/annotate-next", methods=["GET", "POST"])
def annotate_next():
    return annotate_paginate(True)

@route("/annotate/<:id>", methods=["GET"])
def annotate_id(id: int):
    return go_to_id(id)

def annotate_paginate(is_forward: bool):
    modifier = 1 if is_forward else -1

@route("/annotate", methods=["GET", "POST"])
def annotate_page():
    """
    Parses the input received from the user's annotation and takes some action
    based on what was clicked/typed. This method is the main switch for changing
    the state of the server for this user.
    """
    if not is_logged_in(request):
        return render_template(
            "error.html",
            error_message="Please login to annotate or you are using the wrong link",
        )
    
    action = request.form.get("src") if action is None else action
    if action is None:
        return render_template(
            "error.html",
            error_message="Please login to annotate or you are using the wrong link",
        )
    
    viable_actions = {
        "home": annotate_home,
        "prev_instance": lambda : annotate_paginate(False),
        "next_instance": lambda : annotate_paginate(True),
        "go_to": lambda: annotate_id(request.form.get("go_to"))
    }

    if not action in viable_actions.keys():
        print('unrecognized action request: "%s"' % action)
        return render_template(
            "error.html",
            error_message="Please login to annotate or you are using the wrong link",
        )

    return viable_actions[action]()

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
