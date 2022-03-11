import yaml
import pkg_resources

from poktbot.log.poktbot_logging import poktbot_logging
from poktbot.utils import DotDict


class Config(DotDict):
    """
    Class to centralize all the configurations.
    """
    def __init__(self, filename=None, config_scheme=None, *args, **kwargs):
        self._logger = poktbot_logging.get_logger("config")
        self._filename = filename

        if config_scheme is None:
            with open(pkg_resources.resource_filename("poktbot", "config/config_scheme.yaml"), "r") as f:
                config_scheme = yaml.safe_load(f)
            self._logger.debug("Loaded default scheme for config succesfully")

        self._config_scheme = config_scheme

        super().__init__(*args, **kwargs)

    def evaluate_scheme(self):
        """
        Ensures that required config options are set.
        :return: True if evaluated successfully. False otherwise.
        """
        for scheme in self._config_scheme:
            if scheme['key'] not in self:
                if 'default_value' not in scheme:
                    self._logger.error(f"Missing mandatory key {scheme['key']} in the config file")
                    return False

                else:
                    self._logger.warning(f"Missing optional key {scheme['key']}. Default value was set: {scheme['default_value']}")
                    self[scheme['key']] = scheme['default_value']

        return True

    def save(self):
        """
        Saves the config into the file.
        """
        raise NotImplementedError()
