"""

"""

import os
import logging

_logger = logging.getLogger("TemplateModuleValidation")

def valid_absolute_path_or_raise(
        html_file_type, 
        selected_path, 
        config_path
    ):

    _logger.info(
        f"{html_file_type} will be loaded from user-defined file {selected_path}"
    )
    
    if os.path.exists(selected_path):
        return selected_path

    # See if we can get it from the relative path
    real_path = os.path.realpath(config_path)
    dir_path = os.path.dirname(real_path)
    abs_file = os.path.join(dir_path, selected_path)

    if not os.path.exists(abs_file):
        raise FileNotFoundError(f"{html_file_type} not found: {abs_file}")

    return abs_file