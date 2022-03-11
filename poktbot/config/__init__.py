"""
Module to handle configuration files.

A config interface is defined in `config.py`. Every config parser is defined in a subfolder.
"""
from poktbot.config.ini.config import ConfigINI
from poktbot.config.yaml.config import ConfigYAML
from poktbot.config.json.config import ConfigJSON
from poktbot.config.os.config import ConfigOS
from poktbot.log import poktbot_logging

import pkg_resources
import os


AVAILABLE_CONFIG_PARSERS = {
    ConfigYAML.FILENAME_EXTENSION: ConfigYAML,
    ConfigINI.FILENAME_EXTENSION: ConfigINI,
    ConfigJSON.FILENAME_EXTENSION: ConfigJSON,
    # The OS config parser is excluded from here as its data is retrieved from the environment variables.
}


def no_available_parsers(filename):
    raise KeyError(f'No parser available for the config "{filename}"')


# If no config path is provided, it will be generated in this path. For example: if configured through environment vars
DEFAULT_CONFIG_PATH = "/etc/poktbot/config.yaml"


# Those are the paths where we are going to look for a config file, in order.
CONFIG_PATHS = [
    # This path can be set as an environment variable, which has priority over the rest.
    os.environ.get("CONFIG_PATH", DEFAULT_CONFIG_PATH),

    # Default locations in an installed environment / Docker image.
    "/etc/poktbot/config.ini",
    "/etc/poktbot/config.json",

    # In case it is stored in the library local path.
    pkg_resources.resource_filename("poktbot", "../config/config.ini"),
    pkg_resources.resource_filename("poktbot", "../config/config.yaml"),
    pkg_resources.resource_filename("poktbot", "../config/config.json"),
]


# Global scoped configuration object. This config can be fetched by calling `get_config()`
_poktbot_config = None


def load_config(path, must_exist=True):
    """
    Tries to load the config from the given path.

    :param path:
        path to load the config from.

    :param must_exist:
        Boolean flag specifying if file must exist or not. Defaults to True.
        If the flag is set to True and the file does not exist, a FileNotFoundError will be raised.

    :return:
        Config object represented in that path.
    """
    if path is None:
        path = ''
        
    if not os.path.exists(path) and must_exist:
        raise FileNotFoundError(f"The path for the configuration ({path}) file does not exist")

    filename_extension = path.rsplit(".", 1)[1].lower()
    config = AVAILABLE_CONFIG_PARSERS.get(filename_extension, no_available_parsers)(path)

    return config


def get_config(path=None):
    """
    Global singleton for retrieving the config file.

    The first time this function is called, it will try to load the config file and store it in a global scope unless a
    path is provided, which forces a reload.

    Rest of the calls without providing a path returns the same config object.

    Note that environment variables have priority, hence they can override any configuration option.

    :param path:
        Path URI to the configuration file to be loaded from. Supported formats are: .ini, .yaml or .json.

        If a path is provided, the config will be forcefully reloaded.

        If a path is not provided:
          1. If a config is already loaded, the same config will be returned.
          2. If the config is not loaded, it will try to load from all the known paths or the environment variables.

    :return:
        The configuration object (dictionary).

        If not file was found but options were retrieved from env vars, the config file will be pointing to the path
        specified in `DEFAULT_CONFIG_PATH`.
    """
    global _poktbot_config

    # If a path is provided, the config will be forcefully reloaded.
    if path is not None:
        _poktbot_config = load_config(path, must_exist=True)
        _poktbot_config.evaluate_scheme()

    elif _poktbot_config is None:
        for config_path in CONFIG_PATHS:
            try:
                _poktbot_config = load_config(config_path)
            except FileNotFoundError:
                continue

            break

        # If no config file was found, we create one in the default path. Options could still be in the environment vars
        if _poktbot_config is None:
            config_path = DEFAULT_CONFIG_PATH
            try:
                with open(config_path, "w") as f:
                    pass
            except FileNotFoundError:
                config_path = "config.yaml"
                with open(config_path, "w") as f:
                    pass

            _poktbot_config = load_config(config_path)

        # Finally we override any configuration by the ones found in the environment vars.
        config_os = ConfigOS()

        for k, v in config_os.items():
            _poktbot_config[k] = v

        _poktbot_config.evaluate_scheme()

        # We pick file paths in config so that we create their paths:
        logging_path = os.path.dirname(_poktbot_config.get("SERVER.log_file_location", ""))
        session_path = os.path.dirname(_poktbot_config.get("TELEGRAM_API.session_path", "") + "/")
        database_path = os.path.dirname(_poktbot_config.get("SERVER.database_location", ""))

        if logging_path != "":
            os.makedirs(logging_path, exist_ok=True)
        if session_path != "":
            os.makedirs(session_path, exist_ok=True)
        if database_path != "":
            os.makedirs(database_path, exist_ok=True)

        # If a file was specified for storing logging information, we set it up here
        logging_file = _poktbot_config.get("SERVER.log_file_location", "")

        if logging_file != "":
            poktbot_logging.add_file_handler(logging_file)

    return _poktbot_config


__ALL__ = ["get_config", "ConfigINI", "ConfigYAML", "ConfigJSON", "ConfigOS"]
