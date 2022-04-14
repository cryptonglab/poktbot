from poktbot.api import get_observer
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.constants import __version__

import pandas as pd


class CallbackNotifyRelease:
    """
    Callback invoked when a new bot release is detected.

    This is usually invoked after all the prices from a price provider is fetched.
    """

    def __init__(self, bot):
        self._logger = poktbot_logging.get_logger("CallbackNotifyRelease")
        self._bot = bot

    def __call__(self, *args, **kwargs):

        config = get_config()
        allow_notification = config['CONF.notify_releases']
        docs_url = config['CONF.release_docs']

        target_entities = pd.Series(config['IDS.admins_ids']).unique().tolist()  # type: list
        observer_releases = get_observer("releases")

        pypi_release = observer_releases[0]

        if pypi_release.latest_version != __version__ and allow_notification:
            self._logger.info(f"Triggered notification of new release to admins ({target_entities})")
            for entity in target_entities:
                self._bot.send_message(entity, f"New PoktBot release available: {pypi_release.latest_version}\n({docs_url})")
