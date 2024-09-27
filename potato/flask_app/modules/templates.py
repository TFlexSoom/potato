cur_working_dir = os.getcwd() #get the current working dir
cur_program_dir = os.path.dirname(os.path.abspath(__file__)) #get the current program dir (for the case of pypi, it will be the path where potato is installed)
flask_templates_dir = os.path.join(cur_program_dir,'templates') #get the dir where the flask templates are saved
base_html_dir = os.path.join(cur_program_dir,'base_htmls') #get the dir where the the base_html templates files are saved

#insert the current program dir into sys path
sys.path.insert(0, cur_program_dir)


#mapping the base html template str to the real file
template_dict = {
    "base_html_template":{
        'base': os.path.join(cur_program_dir, 'base_html/base_template.html'),
        'default': os.path.join(cur_program_dir, 'base_html/base_template.html'),
    },
    "header_file":{
        'default': os.path.join(cur_program_dir, 'base_html/header.html'),
    },
    "html_layout":{
        'default': os.path.join(cur_program_dir, 'base_html/examples/plain_layout.html'),
        'plain': os.path.join(cur_program_dir, 'base_html/examples/plain_layout.html'),
        'kwargs': os.path.join(cur_program_dir, 'base_html/examples/kwargs_example.html'),
        'fixed_keybinding': os.path.join(cur_program_dir, 'base_html/examples/fixed_keybinding_layout.html')
    },
    "surveyflow_html_layout": {
        'default': os.path.join(cur_program_dir, 'base_html/examples/plain_layout.html'),
        'plain': os.path.join(cur_program_dir, 'base_html/examples/plain_layout.html'),
        'kwargs': os.path.join(cur_program_dir, 'base_html/examples/kwargs_example.html'),
        'fixed_keybinding': os.path.join(cur_program_dir, 'base_html/examples/fixed_keybinding_layout.html')
    }
}


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