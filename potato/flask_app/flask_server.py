"""
Driver to run a flask server.
"""
import atexit
import logging
from flask import Flask
from potato.server_utils.arg_utils import arguments
from potato.server_utils.config import from_cli_args
from potato.server_utils.cache import singleton
from potato.server_utils.module import configure, start, cleanup
from potato.flask_app.modules.app import set_logging_verbosity, get_port, is_very_verbose

@singleton
def get_app():
    return Flask(__name__)

def run_server(args):
    # There are many flask integrations which require 'app' be
    #   globally public, however, it will be best to keep this
    #   non-global within potato to reduce global scope
    # 
    #   Per these integrations, create an auxilliary script and call
    #   get_app after run_server in a global variable such that 
    #   `flask_server` is imported but not tainted
    app = get_app()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig()

    from_cli_args(args)
    configure()
    set_logging_verbosity()
    start()


    flask_logger = logging.getLogger("werkzeug")
    flask_logger.setLevel(logging.ERROR)
    
    port = get_port()
    print("running at:\nlocalhost:" + str(port))
    atexit.register(lambda: cleanup())
    app.run(debug=is_very_verbose(), host="0.0.0.0", port=port)


def main():
    args = arguments()
    run_server(args)

if __name__ == "__main__":
    main()
