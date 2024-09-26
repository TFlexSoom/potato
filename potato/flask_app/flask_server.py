"""
Driver to run a flask server.
"""
import os
import logging
import random
from collections import deque, defaultdict
import yaml
from flask import Flask

from server_utils.arg_utils import arguments
from potato.server_utils.config import init_config, get_config
from potato.flask_app.modules.front_end import generate_site, generate_surveyflow_pages
from potato.flask_app.modules.prolific_apis import ProlificStudy
from server_utils.cache import singleton

"""
    domain_file_path = ""
    file_list = []
    file_list_size = 0
    default_port = 8000
    user_dict = {}

    file_to_read_from = ""

    user_story_pos = defaultdict(lambda: 0, dict())
    user_response_dicts_queue = defaultdict(deque)

    # A global mapping from username to the annotator's
    user_to_annotation_state = {}

    # A global mapping from an instance's id to its data. This is filled by
    instance_id_to_data = {}

    # A global dict to keep tracking of the task assignment status
    task_assignment = {}

    # This variable of tyep ActiveLearningState keeps track of information on active
    # learning, such as which instances were sampled according to each strategy
    active_learning_state = None

    # Hacky nonsense
    schema_label_to_color = {}

"""

def run_server(args):
    """
    Run Flask server.
    """
    

    app = Flask(__name__)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig()

    init_config(args)
    if get_config().verbose:
        logger.setLevel(logging.DEBUG)
    if get_config().very_verbose:
        logger.setLevel(logging.NOTSET)

    user_config = UserConfig(USER_CONFIG_PATH)

    #load prolific configurations
    if get_config().prolific and get_config().prolific['config_file_path']:
        # load multitask annotation config
        with open(get_config().prolific['config_file_path'], "rt") as f:
            prolific_config = yaml.safe_load(f)
            max_concurrent_sessions = prolific_config.get('max_concurrent_sessions') if prolific_config.get('max_concurrent_sessions') else 30
            workload_checker_period = prolific_config.get('workload_checker_period') if prolific_config.get('workload_checker_period') else 300
            prolific_study = ProlificStudy(prolific_config['token'], prolific_config['study_id'],
                                           saving_dir = get_config().output_annotation_dir,
                                           max_concurrent_sessions=max_concurrent_sessions,
                                           workload_checker_period=workload_checker_period)
        study_basic_info = prolific_study.get_basic_study_info()
        print('Prolific configurations successfully loaded for study: %s'%study_basic_info['internal_name'])
        for k,v in study_basic_info.items():
            print("%s: %s"%(k, v))

        #overide the login setting as prolific
        get_config().login['type'] = 'prolific'

        #update the submission status
        #prolific_study.update_submission_status()
        #users_to_drop = prolific_study.get_dropped_users()
        #remove_instances_from_users(users_to_drop)

    #load user configuration settings and add authorized users
    user_config_data = get_config().user_config_file
    if 'allow_all_users' in user_config_data:
        user_config.allow_all_users = user_config_data['allow_all_users']

        if 'authorized_users' in user_config_data:
            for user in user_config_data["authorized_users"]:
                user_config.authorized_users.append(user)


    # set up the template file path
    for key in ["html_layout", "surveyflow_html_layout", "base_html_template", "header_file"]:
        # if template not set in the configuration file, use the default version
        if key not in config:
            logger.warning("%s not configured, use default template at %s"%(key, template_dict[key]['default']))
            config[key] = template_dict[key]['default']
        # if user uses a template in the lib, replace the key with the file location
        elif config[key] in template_dict[key]:
            config[key] = template_dict[key][config[key]]
        # if user uses a self defined file, directly use it as the template
        else:
            logger.info("%s will be loaded from user-defined file %s" % (key,config[key]))

    #overwrite the site_dir to the default path, this will not be shown to the users
    #todo: remove all the site_dir key from the configuration files or figure out a way to handle render flask templates from different dirs
    #todo: having the flask templates in the user-defined project folder would be neccessary in the long run due to potential conflicts of projects with the same name
    # each project dir should be self-contained, even for the flask template files
    config["site_dir"] = flask_templates_dir
    # Creates the templates we'll use in flask by mashing annotation
    # specification on top of the proto-templates
    generate_site(config)
    if "surveyflow" in config and config["surveyflow"]["on"]:
        generate_surveyflow_pages(config)

    # Generate the output directory if it doesn't exist yet
    if not os.path.exists(config["output_annotation_dir"]):
        os.makedirs(config["output_annotation_dir"])

    # Loads the training data
    load_all_data(config)

    # load users with annotations to user_to_annotation_state
    users_with_annotations = [
        f
        for f in os.listdir(config["output_annotation_dir"])
        if os.path.isdir(os.path.join(config["output_annotation_dir"],f)) and f != 'archived_users'
    ]
    for user in users_with_annotations:
        load_user_state(user)

    # TODO: load previous annotation state
    # load_annotation_state(config)

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.setLevel(logging.ERROR)

    port = args.port or config.get("port", default_port)
    print("running at:\nlocalhost:" + str(port))
    app.run(debug=args.very_verbose, host="0.0.0.0", port=port)


def main():
    args = arguments()
    run_server(args)

if __name__ == "__main__":
    main()
