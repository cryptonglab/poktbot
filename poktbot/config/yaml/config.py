import yaml

from poktbot.config.config import Config
from poktbot.log import poktbot_logging


class ConfigYAML(Config):
    FILENAME_EXTENSION = "yaml"

    def __init__(self, filename):
        logger = poktbot_logging.get_logger('config')

        try:
            with open(filename, "r") as f:
                config_dictionarized = yaml.safe_load(f)

            if config_dictionarized is None:
                config_dictionarized = {}

            logger.info(f'Config "{filename}" loaded successfully')

        except yaml.YAMLError as e:
            logger.error(f'Error loading config "{filename}" : {str(e)}. Aborted')
            raise e

        super().__init__(filename, None, config_dictionarized)

    def save(self):
        with open(self._filename, 'w') as f:
            yaml.dump(self.to_dict(), f, indent=4)
