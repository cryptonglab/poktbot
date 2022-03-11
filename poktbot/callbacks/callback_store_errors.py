import pandas as pd

from poktbot.api import get_observer
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb


class CallbackStoreErrors:
    """
    Callback invoked when the cached errors data should be stored in a database.

    This is usually invoked after all the nodes information and the prices from a price provider is fetched.
    """

    def __init__(self, notify_callback=None):
        self._logger = poktbot_logging.get_logger("CallbackStoreErrors")
        self._notify_callback = notify_callback

    def __call__(self, *args, **kwargs):
        self._logger.debug("Triggered store of errors (if any)")

        config = get_config()
        observer_nodes_errors = get_observer("nodes_errors")
        errors_db = get_relaydb("errors")
        errors_notification_min_date = pd.Timestamp.now("UTC") \
                                      - pd.Timedelta(**((lambda x: {x[1]: int(x[0])})(config["SERVER.errors_notification_max_age"].split(" "))))

        # Notifications to telegram are queued here and notified at the end of the function
        pending_notifications = []

        # TODO: if the number of tracked nodes is large, we need to make the bulk operation inside the loop not outside.
        #       But, we also need to change the DB backend.
        with errors_db.bulk_op() as db:

            for node in observer_nodes_errors:
                # We fetch the last information stored for this node.
                node_db_persistence = db.setdefault(node.address, {})
                errors_df = node.errors

                # If no errors, skip the node
                if errors_df is None or errors_df.shape[0] == 0:
                    continue

                # Otherwise, we go for each error rule to notify as expected
                error_rules = config["SERVER.error_rules"]

                # We store the errors in the database concating them to the previous
                # It is guaranteed that there are no duplicates, so concating should be safe.
                # Either ways, we ensure it with .drop_duplicates()
                node_errors = node_db_persistence.setdefault("errors", errors_df.iloc[0:0])
                node_errors = pd.concat([node_errors, errors_df], axis=0).drop_duplicates()
                node_db_persistence["errors"] = node_errors
                self._logger.info(f"Stored {errors_df.shape[0]} new errors in database for node {node.address}")

                # Now we store the status for this node errors
                node_db_persistence["last_error_date"] = node.last_error_date

                # Now the notify process.
                for error_rule in error_rules:

                    # Select the rows that contain the expected message
                    sub_errors_df = errors_df[errors_df['message'].str.contains(error_rule['find'])]

                    # Errors should be younger than max allowed age for errors
                    sub_errors_df = sub_errors_df[sub_errors_df['time'] > errors_notification_min_date]

                    if sub_errors_df.shape[0] == 0:
                        continue

                    template_msg_single = error_rule.get('notify_single')
                    template_msg_many = error_rule.get('notify_many')

                    # We add to the queue the notifications. Notifications are performed outside the bulk context
                    # because it might take time and the bulk operation holds a lock in the database. This way lock
                    # is released faster.
                    if template_msg_single is not None or template_msg_many is not None:
                        pending_notifications.append({
                            'node_address': node.address,
                            'errors_df': sub_errors_df,
                            'template_msg_single': template_msg_single,
                            'template_msg_many': template_msg_many,
                        })

        # Notifications to telegram
        if len(pending_notifications) > 0 and self._notify_callback is not None:
            self._notify_callback(pending_notifications)
