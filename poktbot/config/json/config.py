import json

from poktbot.config.config import Config
from poktbot.log import poktbot_logging


class ConfigJSON(Config):
    FILENAME_EXTENSION = "json"

    def __init__(self, filename):
        logger = poktbot_logging.get_logger('config')

        try:
            with open(filename, "r") as f:
                config_dictionarized = json.load(f)

            if config_dictionarized is None:
                config_dictionarized = {}

            logger.info(f'Config "{filename}" loaded successfully')

        except json.JSONDecodeError as e:
            logger.error(f'Error loading config "{filename}" : {str(e)}. Aborted')
            raise e

        super().__init__(filename, None, config_dictionarized)

    def save(self):
        with open(self._filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
