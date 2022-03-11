import pandas as pd

from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.utils.formatting import format_date


class CallbackNotifyErrors:
    """
    Callback invoked when the errors should be notified to the clients.

    This callback will be executed every time after all nodes information is fetched.
    """
    def __init__(self, bot):
        self._bot = bot
        self._logger = poktbot_logging.get_logger("CallbackNotifyErrors")

    def __call__(self, pending_notifications, *args, **kwargs):

        for pending_notification in pending_notifications:
            errors_df = pending_notification['errors_df']
            node_address = pending_notification['node_address']
            template_msg_single = pending_notification['template_msg_single']
            template_msg_many = pending_notification['template_msg_many']

            # If there are more than 1 error, we pack them by begintime-endtime
            if errors_df.shape[0] > 1:
                row = errors_df.iloc[0].copy()
                row["count"] = errors_df.shape[0]
                row["begintime_formatted"] = format_date(errors_df["time"].min())
                row["endtime_formatted"] = format_date(errors_df["time"].max())
                message = template_msg_many.format(address=node_address, **row.to_dict())

            else:  # Otherwise, we notify the exact error.
                row = errors_df.iloc[0].copy()
                row.loc["time_formatted"] = format_date(errors_df['time'])
                message = template_msg_single.format(address=node_address, **row.to_dict())

            self._notify(message)

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
