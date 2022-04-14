
from poktbot.api.node.node import PocketNode
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb
from poktbot.utils.decorators import retry
from poktbot.utils.formatting import format_date

import pandas as pd
import requests


class PocketNodeTransactions(PocketNode):
    """
    Represents a PocketNode with basic API implementation for fetching transactions.

    Usage example:
        >>> from poktbot.api.node import PocketNodeTransactions
        >>> node_transactions = PocketNodeTransactions("047fe6618553aba4816d948aca98808c3eb1ad38")
        >>> node_transactions.update()

        >>> node_transactions.transactions

        [{'wallet': '047fe6618553aba4816d948aca98808c3eb1ad38',
        'hash': '23E4F9932B073491090E55A85B5C4C2B66AFBB2E4FC5F624D6FC6AF613898EF2',
        'type': 'proof',
        'chain_id': 'Gnosis Chain',
        'height': 50746,
        'time': Timestamp('2022-02-12 06:29:06.492000+0000', tz='UTC'),
        'amount': 2.5365,
        'memo': ''},
        {'wallet': '047fe6618553aba4816d948aca98808c3eb1ad38',
        'hash': '039628C0B835E871FAC595D8E80DEA9060714A6CD2B3C6A4F86510898E1D5173',
        'type': 'send',
        'chain_id': '',
        'height': 50735,
        'time': Timestamp('2022-02-12 03:41:24.167000+0000', tz='UTC'),
        'amount': 119.7362,
        'memo': 'C0D3R offline wallet transfer'},
        ...
    """

    def __init__(self, node_address, api_url=None, chain_ids=None, initial_height=None, in_staking=None):
        config = get_config()
        relay_db = get_relaydb("transactions")

        # We load start page and initial transactions from the database (if not provided)
        node_db_persistence = relay_db.get(node_address, {})

        if initial_height is None:
            initial_height = node_db_persistence.get("last_height", 1)

        if in_staking is None:
            in_staking = node_db_persistence.get("in_staking", False)

        self._logger = poktbot_logging.get_logger("PocketNodeAPITransactions")

        api_url = api_url or config.get("SERVER.api_url_rewards").format(node_address=node_address)
        super().__init__(node_address, api_url)

        self._chain_ids = chain_ids or config.get("SERVER.chain_ids")
        self._transactions_df = None

        self._last_height = initial_height
        self._in_staking = int(in_staking)

        self._logger.info(f"{self} instantiated")

    @property
    def last_height(self):
        return self._last_height

    @property
    def in_staking(self):
        return self._in_staking

    def rollback(self, height):
        self._last_height = height
        self._transactions_df = None

    @retry(max_attempts=3, attempt_interval=5, on_exception=requests.exceptions.RequestException)
    @retry(max_attempts=3, attempt_interval=5, on_exception=LookupError)
    def _request_rewards(self):
        """
        Requests the rewards to the HTTP api url and returns the JSON.
        The rewards are the claim/proof transactions.
        """
        self._logger.debug(f"{self} Requesting rewards transactions")
        response = requests.get(self._api_url)

        if response.status_code != 200:
            raise LookupError(f"Not 200 status code; error: {response.status_code}")

        self._logger.debug(f"{self} Response: {response.status_code}")

        return response.json()

    def _fetch_transactions(self):
        """
        Fetches all the transactions from the last cached transaction until the last one.

        This method does not update the last_update attribute of this class. The method `update()` is preferred instead.

        Transactions are stored within the object and can be accessed through the property `.transactions`.

        This method overrides the .transactions dataframe with the last snapshot, which won't include the transactions
        from the previous snapshot.
        """
        config = get_config()

        date_format = config["SERVER.api_date_format"]

        self._logger.info(f"{self} Requesting transactions...")

        # 1. Request rewards transactions
        rewards = self._request_rewards()

        # 2. Give format to the rewards
        rewards_parsed = []
        for c in rewards['data']:
            for tr in c['transactions']:
                rewards_parsed.append(self._build_transaction_reward_element(tr, date_format))

        rewards_df = pd.DataFrame(rewards_parsed)

        # The rewards API does not filter by height, so we must ensure we don't pick rewards already stored
        rewards_df = rewards_df[rewards_df['height'] > self._last_height]

        # We merge the rewards_df into the transactions_df
        transactions_df = rewards_df.sort_values("height").reset_index(drop=True)
        transactions_df["in_staking"] = 1  # Temporal workaround

        self._logger.info(f"{self} Found {transactions_df.shape[0]} new transactions")

        with self._lock:
            self._transactions_df = transactions_df

            if transactions_df.shape[0] > 0:
                self._last_height = transactions_df['height'].max()
                self._in_staking = transactions_df['in_staking'].iloc[-1]

    def _build_transaction_reward_element(self, transaction_reward_raw_item, date_format):
        """
        Builds the transaction element from the transaction item retrieved from rewards API
        """
        transaction_time = pd.to_datetime(transaction_reward_raw_item["time"], format=date_format)

        amount = transaction_reward_raw_item['num_relays'] * transaction_reward_raw_item['pokt_per_relay']

        transaction = {
            "wallet": self.address,
            "hash": transaction_reward_raw_item["hash"],
            "type": "claim",
            "chain_id": self._chain_ids.get(transaction_reward_raw_item["chain_id"], ''),
            "height": transaction_reward_raw_item["height"],
            "time": transaction_time,
            "amount": amount,
            "memo": "",
            "confirmed": transaction_reward_raw_item['is_confirmed'],
        }

        return transaction

    @property
    def transactions(self):
        """
        Retrieves the last cached transactions from this node instance.
        Transactions should be updated by calling `update()` or `update_transactions()` first.
        """
        return self._transactions_df

    def update(self):
        """
        Updates the node information from the node API URL.
        """
        super().update()
        self._fetch_transactions()

    def __str__(self):
        return f"[poktbot - Node {self.address} (transactions); last update: {format_date(self.last_update)}; " \
               f"transactions count: {self._transactions_df.shape[0] if self._transactions_df is not None else 0}; " \
               f"in staking: {self.in_staking}]"

    def __repr__(self):
        return str(self)
