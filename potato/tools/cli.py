#!/usr/bin/env python

import sys

from potato.flask_app.flask_server import run_server
from server_utils.arg_utils import arguments
from tool_utils.cli_utils import get_project_from_hub, show_project_hub
from potato import *
from potato.tools.create_task_cli import create_task_cli, yes_or_no

MODES = {
    'start': run_server,
    'get': get_project_from_hub,
    'list': show_project_hub,
}

# referenced by setup.py
def potato():
    
    # Run task configuration script if no arguments are given.
    if len(sys.argv) == 1:
        run_create_task_cli()
        return
    
    args = arguments()
    if args.mode not in MODES:
        raise RuntimeError(f"{args.mode} does not exist as a mode!")
    
    MODES[args.mode](args)

def run_create_task_cli():
    if yes_or_no("Launch task creation process?"):
        create_task_cli()

if __name__ == '__main__':
    potato()
