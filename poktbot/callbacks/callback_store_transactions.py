from poktbot.api import get_observer
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb

import pandas as pd
import numpy as np

from poktbot.utils.formatting import format_date


class CallbackStoreTransactions:
    """
    Callback invoked when the cached transactions data should be stored in a database.

    This is usually invoked after all the nodes information and the prices from a price provider is fetched.
    """
    def __init__(self, notify_staking_callback=None):
        self._logger = poktbot_logging.get_logger("CallbackStoreTransactions")
        self._notify_staking_callback = notify_staking_callback

    def __call__(self, *args, **kwargs):
        self._logger.debug("Triggered store of transactions (if any)")
        config = get_config()
        relay_db = get_relaydb("transactions")
        observer_nodes_transactions = get_observer("nodes_transactions")
        observer_prices = get_observer("prices")

        currency = config.get("PRICE.currency", "eur")

        # Notifications to telegram are queued here and notified at the end of the function
        pending_notifications = []

        with relay_db.bulk_op() as db:

            for node in observer_nodes_transactions:
                # We fetch the last information stored for this node.
                node_db_persistence = db.setdefault(node.address, {})

                transactions_df = node.transactions    # Columns: ['wallet', 'hash', 'type', 'chain_id', 'height', 'time', 'amount', 'memo', 'in_staking']
                prices_df = observer_prices[0].prices  # Columns: ['prices', 'market_caps', 'total_volumes']

                # For each set of transactions, we compute the prices
                if transactions_df is None or prices_df is None or transactions_df.shape[0] == 0 or \
                        prices_df.shape[0] == 0:

                    # If there are transactions but prices couldn't be fetched, we revert back the last transaction date
                    if transactions_df is not None and transactions_df.shape[0] > 0:
                        rollback_height = transactions_df['height'].min() - 1
                        self._logger(f"Warning: transactions are rollbacked to height {rollback_height} because prices couldn't be fetched.")
                        node.rollback(height=transactions_df['height'].min() - 1)

                    continue

                price_indexes = self._get_closest_value(transactions_df["time"], prices_df)

                transactions_prices = prices_df.loc[price_indexes, "prices"]
                transactions_df[f'price_{currency}'] = transactions_prices.values
                transactions_df[f'amount_price_{currency}'] = transactions_df[f'price_{currency}'] * transactions_df['amount']

                # All the operations in the database are updated in bulk
                # We store the transactions in the database concating them to the previous
                # It is guaranteed that there are no duplicates, so concating should be safe.
                # Either ways, we ensure it with .drop_duplicates()
                node_transactions_original = node_db_persistence.setdefault("transactions", transactions_df.iloc[0:0])
                node_transactions = pd.concat([node_transactions_original, transactions_df], axis=0)
                node_db_persistence["transactions"] = node_transactions

                # Now we store the status for this node transactions
                node_db_persistence["current_page"] = node.current_page
                node_db_persistence["last_height"] = node.last_height
                node_db_persistence["in_staking"] = node.in_staking

                self._logger.info(f"Stored {transactions_df.shape[0]} new transactions in database for node {node.address}")

                # We check for staking transactions:
                transactions_df_staking = transactions_df[transactions_df['type'].str.contains('stake')]

                for idx, row in transactions_df_staking.iterrows():
                    if row["type"] == "stake_validator":
                        message = f"\U0001F389 \U0001F389\n \U0001F5A5 {row['wallet']}\n \U0001F4C5 {format_date(row['time'])}\n \u2709 Started staking."
                    else:
                        message = f"\u26A0 \u26A0\n \U0001F5A5 {row['wallet']}\n \U0001F4C5 {format_date(row['time'])}\n \u2709 Begin unstake validator."

                    pending_notifications.append(message)

        # Notifications to telegram
        if len(pending_notifications) > 0 and self._notify_staking_callback is not None:
            self._notify_staking_callback(pending_notifications)

    @staticmethod
    def _get_closest_value(datetimes, values_to_lookup):
        """
        Computes the closest row for the given list of datetimes.

        :param datetimes:
            List/array/series of datetimes to match with values_to_lookup.

        :param values_to_lookup:
            Series/Dataframe of values indexed by timestamps.
        """
        values_to_lookup = values_to_lookup.index if hasattr(values_to_lookup, "index") else values_to_lookup

        transaction_times = datetimes.view("int64") // 10 ** 6
        min_index = np.abs(
                        np.expand_dims(values_to_lookup, axis=0) - np.expand_dims(transaction_times, axis=1)
                    ).argmin(axis=1)

        closest_values = values_to_lookup[min_index]
        return closest_values
