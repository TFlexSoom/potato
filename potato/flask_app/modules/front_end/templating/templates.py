# Probably should be a set of enums or a database lookup but only the OSS will
#  use these templates so going to leave as is for now.
from dataclasses import dataclass
import logging
from typing import NewType

_logger = logging.getLogger("TemplateModuleValidation")

HTML_TEMPLATE_DICT = {
    "base_html_template":{
        'base': 'base_html/base_template.html',
        'default': 'base_html/base_template.html',
    },
    "header_file":{
        'default': 'base_html/header.html',
    },
    "html_layout":{
        'default': 'base_html/examples/plain_layout.html',
        'plain': 'base_html/examples/plain_layout.html',
        'kwargs': 'base_html/examples/kwargs_example.html',
        'fixed_keybinding': 'base_html/examples/fixed_keybinding_layout.html'
    },
    "surveyflow_html_layout": {
        'default': 'base_html/examples/plain_layout.html',
        'plain': 'base_html/examples/plain_layout.html',
        'kwargs': 'base_html/examples/kwargs_example.html',
        'fixed_keybinding': 'base_html/examples/fixed_keybinding_layout.html'
    }
}

TemplatePath = NewType('TemplatePath', str)
Template = NewType('Template', str)

@dataclass
class TemplatePaths:
    html_layout: TemplatePath = ""
    base_html_template: TemplatePath = ""
    header_file: TemplatePath = ""
    surveyflow_html_layout: TemplatePath = ""

@dataclass
class Templates:
    html_layout: Template = ""
    base_html_template: Template = ""
    header_file: Template = ""
    surveyflow_html_layout: Template = ""


def read_html(paths: TemplatePaths):
    templates = Templates()
    layout_fields = HTML_TEMPLATE_DICT.keys()
    for field_name in layout_fields:
        abs_file_path = getattr(paths, field_name)
        _logger.debug(f"Reading {field_name} from {abs_file_path}")

        with open(abs_file_path, "rt") as file:
            setattr(templates, field_name, "".join(file.readlines()))
    
    return templates
