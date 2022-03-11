import configparser

from poktbot.config.config import Config
from poktbot.log import poktbot_logging


class ConfigINI(Config):

    FILENAME_EXTENSION = "ini"

    def __init__(self, filename):
        logger = poktbot_logging.get_logger('config')

        self._filename = filename

        config = configparser.ConfigParser()
        config.read(filename, encoding='utf-8')
        config_dictionarized = self._dictionarize(config)

        if config_dictionarized is None:
            config_dictionarized = {}

        super().__init__(filename, None, config_dictionarized)
        logger.info(f'Config "{filename}" loaded successfully')

    @staticmethod
    def _dictionarize(source):
        """
        Converts the configparser parsed output into a dictionary.

        When a comma sepparated input is found, it is automatically converted to a list.
        """

        if type(source) in [configparser.SectionProxy, configparser.ConfigParser]:
            result = {k: ConfigINI._dictionarize(v) for k, v in source.items()}
        else:
            result = source.split(",") if type(source) is str and "," in source else source

        return result

    def save(self):
        config = configparser.ConfigParser()

        for config_key in self:
            section, option = config_key.split(".", 1)
            value = self[config_key]
            config.set(section, option, value if type(value) is not list else ",".join(value))

        with open(self._filename, 'w') as f:
            config.write(f, space_around_delimiters=True)
