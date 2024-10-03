"""
author: Tristan Hilbert
New Span Layout
"""

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_assigned_colors = {}
span_counter = 0
MAX_SPAN_LABELS = 64
COLOR_MODULO = 24

def _get_span_color(span_label):
    color = _assigned_colors.get(span_label, None)
    if color != None:
        return color
    
    global span_counter
    span_counter += 1
    color = _set_span_color(span_label, span_counter)
    

def _set_span_color(span_label, color):
    _assigned_colors[span_label] = color
    return color

def _to_entry(span_annotation):
    color = _get_span_color(span_annotation["annotation"])
    return {
        "displayed_text": span_annotation["displayed_text"],
        "span_annotations_starts": 
            map(lambda x: x["start"], span_annotation["span_annotations"]), 
        "span_annotations_ends": 
            map(lambda x: x["end"], span_annotation["span_annotations"]),
        "color": color,
        "bg_color": color[:-1] + ",0.25)" # change alpha from color

    }

def render_span_annotations(span_annotations):
    if len(span_annotations) == 0:
        return None

    return json.dumps(map(_to_entry, span_annotations))

@dataclass
class SpanScheme:
    annotation_type: str
    name: str
    description: str
    labels: list[dict] # TODO Labels Object Should be defined
    label_requirement: str
    bad_text_label_content: str
    horizontal: bool
    sequential_key_binding: bool
    displaying_score: bool

def _from_scheme_to_object(scheme):
    labels = scheme.get("labels", [])

    if len(labels) != 0 and isinstance(labels[0], str):
        labels = list(map(lambda x: {"name": x}, labels))

    return SpanScheme(
        annotation_type=scheme.get("annotation_type", "beta_highlight"),
        name=scheme.get("name", "default"),
        description=scheme.get("description", ""),
        labels=labels,
        label_requirement=scheme.get("label_requirement", ""),
        bad_text_label_content=scheme.get("bad_text_label", {}).get("label_content", ""),
        horizontal=scheme.get("horizontal", False),
        sequential_key_binding=scheme.get("sequential_key_binding", True),
        displaying_score=scheme.get("displaying_score", False)
    )

def _get_key_bind(is_sequential: bool, config_val: Optional[str], label_name: str, key2label: dict):
    if is_sequential:
        return len(key2label)
    
    other_label = label_name
    if config_val != None:
        other_label = key2label.get(config_val, label_name)
    
    if other_label != label_name:
        raise RuntimeError(f"Keyboard input conflict: {config_val}")
    
    return config_val

def generate_label_inputs(span_scheme):
    key2label = {}
    label_htmls = []
    is_checked = True # check first label
    for label_data in span_scheme.labels:
        label_name = label_data["name"]
        tooltip_text = label_data.get("tooltip", "")
        key_value = label_data.get("key_value")
        name = "span_label:::" + span_scheme.name + ":::" + label_name
        class_name = span_scheme.name
        key_value = name
        color = _get_span_color(label_name)
        label_content = label_name

        key_value = _get_key_bind(
            span_scheme.sequential_key_binding, 
            key_value, 
            label_name,
            key2label
        )

        key2label[key_value] = label_name

        if span_scheme.displaying_score:
            label_content = label_data["key_value"] + "." + label_content
        
        check_html = ''
        if is_checked:
            check_html = 'xchecked="checked"'
            is_checked = False
        
        br_label = "<br/>"
        if span_scheme.horizontal:
            br_label = ""

        label_htmls.append(
            '<input ' +
                f' class=" {class_name} new-span-input " ' +
                ' for_span="true" ' +
                ' type="checkbox" ' +
                f' id="{span_scheme.name}" ' +
                f' name="{name}" ' +
                f' value="{key_value}" ' +
                f' {check_html} ' +
                f' data-color="{color}" ' +
                f' data-label-content="{label_content}" ' +
                f' data-key-value="{key_value}" ' +
                f' validation="{"required" if span_scheme.label_requirement else ""}" ' +
            '>' +
            '<label' + 
                ' class=" new-span-label "' +
                f' for="{name}" ' +
                ' data-toggle="tooltip" ' +
                ' data-html="true" ' +
                ' data-placement="top" ' +
                f' title="{tooltip_text}" '+
            '>' +
                f'<span class=" new-span-color-{color} ">' +
                    f'{label_content}' +
                '</span>' +
            '</label>' +
            f'{br_label}'
        )
    
    return label_htmls

def generate_new_span_layout(annotation_scheme):
    span_scheme = _from_scheme_to_object(annotation_scheme)

    if span_scheme.bad_text_label_content != "":
        span_scheme.labels.append({
            "name": span_scheme.name + ":::bad_text",
        })

    if len(span_scheme.labels) > MAX_SPAN_LABELS:
        raise RuntimeError("Cannot have span scheme with more than 64 labels. Please file issue!")
    
    label_htmls = generate_label_inputs(span_scheme)

    return (
        '<form>' +
            '<fieldset>' +
                f'<legend>{span_scheme.description}</legend>' +
                ("".join(label_htmls)) +
            '</fieldset>' +
        '</form>'
    )
