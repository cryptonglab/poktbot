import pandas as pd

from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.utils.formatting import format_date


class CallbackNotifyStaking:
    """
    Callback invoked when the staking transactions should be notified to the clients.

    This callback will be executed every time after all nodes information is fetched.
    """
    def __init__(self, bot):
        self._bot = bot
        self._logger = poktbot_logging.get_logger("CallbackNotifyErrors")

    def __call__(self, pending_notifications, *args, **kwargs):

        for pending_notification_message in pending_notifications:
            self._notify(pending_notification_message)

    def _notify(self, message):
        """
        Notifies the given message to every admin.
        """
        config = get_config()
        bot = self._bot

        target_entities = pd.Series(config['IDS.admins_ids']).unique().tolist()  # type: list

        # Then, we notify every user of every error:
        self._logger.debug(f"Sending update {message} to entities {target_entities}")
        for entity in target_entities:
            bot.send_message(entity, message)
