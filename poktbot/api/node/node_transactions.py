import json

from poktbot.api.node.node import PocketNode
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb
from poktbot.utils.decorators import retry
from poktbot.utils.formatting import format_date

import pandas as pd
import numpy as np
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

    def __init__(self, node_address, api_url=None, chain_ids=None, start_page=None, initial_height=None,
                 in_staking=None):
        config = get_config()
        relay_db = get_relaydb("transactions")

        # We load start page and initial transactions from the database (if not provided)
        node_db_persistence = relay_db.get(node_address, {})

        if start_page is None:
            start_page = node_db_persistence.get("current_page", 1)

        if initial_height is None:
            initial_height = node_db_persistence.get("last_height", 1)

        if in_staking is None:
            in_staking = node_db_persistence.get("in_staking", False)

        self._logger = poktbot_logging.get_logger("PocketNodeAPITransactions")

        api_url = api_url or config.get("SERVER.api_url_transactions")
        super().__init__(node_address, api_url)

        self._rewards_api_url = config.get("SERVER.api_url_rewards").format(node_address=node_address)
        self._chain_ids = chain_ids or config.get("SERVER.chain_ids")
        self._transactions_df = None

        self._current_page = start_page
        self._last_height = initial_height
        self._in_staking = int(in_staking)

        self._logger.info(f"{self} instantiated")

    @property
    def current_page(self):
        """
        Retrieves the current page number
        """
        with self._lock:
            return self._current_page

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
        response = requests.get(self._rewards_api_url)

        if response.status_code != 200:
            raise LookupError(f"Not 200 status code; error: {response.status_code}")

        self._logger.debug(f"{self} Response: {response.status_code}")

        return response.json()

    @retry(max_attempts=3, attempt_interval=5, on_exception=requests.exceptions.RequestException)
    @retry(max_attempts=3, attempt_interval=5, on_exception=LookupError)
    def _request_transactions(self, limit=1000, direction=1, page=1):
        """
        Requests the transactions to the HTTP api url and returns the JSON.

        :param limit:
            Number of transactions to request.

        :param direction:
            Direction of the transactions (-1 from head or 1 from first)

        :param page:
            Page to fetch. Last page contains fewer elements than transactions_limit.

        :return:
            A JSON object containing all the transactions in RAW format.
        """
        query_filter = json.dumps([
            [
                "from_address",
                "=",
                self.address
            ],
            "or",
            [
                "to_address",
                "=",
                self.address
            ]
        ])

        data = {
            "operationName": "transactions",
            "variables":
                {
                    "search": "",
                    "page": page,
                    "limit": limit,
                    "filter": query_filter,
                    "sort": [
                        {
                            "property": "height",
                            "direction": direction
                        }
                    ]
                },
            "query": "query transactions($page: Int!, $search: String!, $limit: Int!, $sort: [SortInput!], $filter: String) {\n  transactions(\n    search: $search\n    page: $page\n    limit: $limit\n    sort: $sort\n    filter: $filter\n  ) {\n    pageInfo {\n      total\n      __typename\n    }\n    items {\n      hash\n      height\n      amount\n      index\n      memo\n      result_code\n      from_address\n      to_address\n      total_fee\n      total_proof\n      type\n      block_time\n      chain\n      app_public_key\n      claim_tx_hash\n      expiration_height\n      session_height\n      __typename\n    }\n    __typename\n  }\n}\n"
        }

        self._logger.info(f"{self} Requesting transactions to node")
        self._logger.debug(f"{self} Requesting transactions {data}")

        response = requests.post(
            self._api_url,
            json=data
        )

        if response.status_code != 200:
            raise LookupError(f"Not 200 status code; error: {response.status_code}")

        result = response.json()
        items_count = len(result.get('data', {}).get('transactions', {}).get('items', []))

        self._logger.debug(f"{self} Response: {response.status_code}; page: {page}; "
                           f"No. elements retrieved: {items_count}; is last page: {items_count < limit}")

        return result

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
        limit = config["SERVER.api_page_size"]
        max_pages = config["SERVER.api_max_page_count"]

        page_slice = slice(self.current_page,
                           self.current_page + max_pages,
                           1)

        transactions_list = []

        page = 1
        is_last_page = False

        # 1. Request transactions
        for page in range(page_slice.start, page_slice.stop, page_slice.step):
            transactions_raw = self._request_transactions(limit=limit, page=page)
            transactions_items = transactions_raw.get("data", {}).get("transactions", {}).get("items", [])

            transactions_parsed = []

            for tr in transactions_items:
                transaction_parsed = self._build_transaction_element(tr, date_format)
                if transaction_parsed is not None:
                    transactions_parsed.append(transaction_parsed)

            new_transactions_df = pd.DataFrame(transactions_parsed)

            is_last_page = new_transactions_df.shape[0] < limit

            new_transactions_df = new_transactions_df[new_transactions_df['height'] > self._last_height]
            transactions_list.append(new_transactions_df)

            if is_last_page:
                break

        # 2. Request rewards transactions
        rewards = self._request_rewards()

        rewards_parsed = []
        for c in rewards['data']:
            for tr in c['transactions']:
                rewards_parsed.append(self._build_transaction_reward_element(tr, date_format))

        transactions_df = pd.concat(transactions_list, axis=0).reset_index(drop=True)

        rewards_df = pd.DataFrame(rewards_parsed)

        # The rewards API does not filter by height, so we must ensure we don't pick rewards already stored
        rewards_df = rewards_df[rewards_df['height'] > self._last_height]

        # If the transactions_df picked are not reaching the last page, we must cut through the last height of the
        # transactions df because the rewards df contains all the rewards to date.
        if not is_last_page:
            rewards_df = rewards_df[rewards_df['height'] <= transactions_df['height'].max()]

        # We merge the rewards_df into the transactions_df
        transactions_df = pd.concat([transactions_df, rewards_df], axis=0).sort_values("height")

        # Some of the transactions might be in staking period, some others not. We compute them.
        # A column called 'in_staking' is added to the transactions dataframe.
        if transactions_df.shape[0] > 0:
            staking_start = transactions_df["type"] == "stake_validator"
            staking_end = transactions_df["type"] == "begin_unstake_validator"

            staking_mask = np.zeros(transactions_df.shape[0]) * np.nan

            staking_mask[staking_start] = 1
            staking_mask[staking_end] = 0

            if np.isnan(staking_mask[0]):
                staking_mask[0] = self._in_staking

            staking_mask = pd.Series(staking_mask).fillna(method="ffill").values

            transactions_df['in_staking'] = staking_mask

        self._logger.debug(f"{self} Found {transactions_df.shape[0]} new transactions")

        with self._lock:
            self._current_page = page + int(not is_last_page)
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

    def _build_transaction_element(self, transaction_raw_item, date_format):
        """
        Builds the transaction element from the transaction item
        """
        transaction_time = pd.to_datetime(transaction_raw_item["block_time"], format=date_format)

        if transaction_raw_item["type"] in ["proof", "claim"]:
            return None

        amount = transaction_raw_item["amount"] / 1000000

        transaction = {
            "wallet": self.address,
            "hash": transaction_raw_item["hash"],
            "type": transaction_raw_item["type"],
            "chain_id": self._chain_ids.get(transaction_raw_item["chain"], ''),
            "height": transaction_raw_item["height"],
            "time": transaction_time,
            "amount": amount,
            "memo": transaction_raw_item["memo"],
            "confirmed": True,
        }

        return transaction

    @staticmethod
    def _get_corresponding_reward_multiplier(rewards_multiplier_table, datetime):
        """
        Retrieves the corresponding reward multiplier for the given datetime

        :param rewards_multiplier_table:
            DataFrame containing two columns: 'date' with datetime objects UTC; and 'multiplier' with the multiplier
            value.

        :param datetime:
            Datetime object in UTC.

        :returns:
            Reward multiplier as a float value.
        """
        datetime_mask = datetime > rewards_multiplier_table['date']
        selected_rewards_multiplier = rewards_multiplier_table[datetime_mask].tail(1)['multiplier'].iloc[0]

        return float(selected_rewards_multiplier)

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
        return f"[poktbot - Node {self.address} (transactions); last update: {format_date(self.last_update)}; current page: {self.current_page}; transactions count: {self._transactions_df.shape[0] if self._transactions_df is not None else 0}; in staking: {self.in_staking}]"

    def __repr__(self):
        return str(self)
