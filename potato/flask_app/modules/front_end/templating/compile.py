
from dataclasses import dataclass

from potato.flask_app.modules.front_end.templating.templates import Template

@dataclass
class CompileData:
    header: Template = ""
    task_html_layout: str = ""
    codebook_html: str = ""
    annotation_task_name: str = ""
    keybindings_desc: str = ""
    statistics_layout: str = ""

# TODO This should be an actual compile function that takes these "handlebars"
# and replaces instances in the file with a third party library and a dictionary
# generated from the dataclass

def compile_template(template, data: CompileData):
    template = template.replace("{{ HEADER }}", data.header)
    template = template.replace("{{ TASK_LAYOUT }}", data.task_html_layout)
    template = template.replace("{{annotation_codebook}}", data.codebook_html)
    template = template.replace("{{annotation_task_name}}", data.annotation_task_name)
    template = template.replace("{{keybindings}}", data.keybindings_desc)
    template = template.replace("{{statistics_nav}}", data.statistics_layout)
    return template