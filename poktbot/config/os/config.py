import os

from poktbot.config.config import Config
from poktbot.log import poktbot_logging


class ConfigOS(Config):

    def __init__(self, *args, **kwargs):
        logger = poktbot_logging.get_logger("config")

        # In this case, we try to load the config keys from the environment variables
        super().__init__(*args, **kwargs)

        for scheme in self._config_scheme:
            key = scheme['key']
            os_value = os.environ.get(key.replace(".", "_"), None)

            if os_value is not None:
                self[key] = os_value.split(",") if type(os_value) is str and "," in os_value else os_value

        logger.info("Loaded config from environmental variables")
