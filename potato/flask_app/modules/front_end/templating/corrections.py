

from dataclasses import dataclass
from typing import Callable

from potato.flask_app.modules.front_end.front_end import TemplateConfig


@dataclass
class Correction:
    on_configurable: Callable[[TemplateConfig], bool]
    find: str
    replace: str

CORRECTIONS = [
    Correction(
        lambda conf: conf.jumping_to_id_disabled, 
        '<input type="submit" value="go">', 
        '<input type="submit" value="go" hidden>'
    ),
    Correction(
        lambda conf: conf.jumping_to_id_disabled,
        '<input type="number" name="go_to" id="go_to" value="" onfocusin="user_input()"' +
          ' onfocusout="user_input_leave()" max={{total_count}} min=0 required>',
        '<input type="number" name="go_to" id="go_to" value="" onfocusin="user_input()"' +
          ' onfocusout="user_input_leave()" max={{total_count}} min=0 required hidden>',
    ),
    Correction(
        lambda conf: conf.hide_navbar,
        '<div class="navbar-nav">',
        '<div class="navbar-nav" hidden>'
    ),
]

def correct_template(template, configuration):
    for correction in CORRECTIONS:
        if not correction.on_configurable(configuration):
            continue

        template.replace(correction.find, correction.replace)
    
    return template

