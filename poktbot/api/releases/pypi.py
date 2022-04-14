from json import JSONDecodeError

from poktbot.api.api import API
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.constants import __version__


import requests


class PyPI(API):
    """
    Checks at PyPI for new releases and notifies them in case.
    """

    def __init__(self, api_url=None):
        super().__init__()
        config = get_config()

        self._logger = poktbot_logging.get_logger("PyPI")
        self._api_url = api_url or config['CONF.release_url']

        self._latest_version = __version__
        self._logger.debug(f"Initiated PyPI hook for new PoktBot releases notification")

    def update(self):
        response = requests.get(self._api_url)

        try:
            latest_version = response.json()['info']['version']
        except (JSONDecodeError, KeyError) as e:
            latest_version = __version__

        self._latest_version = latest_version

    @property
    def latest_version(self):
        return self._latest_version
