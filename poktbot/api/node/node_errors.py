import requests
import pandas as pd

from poktbot.api.node.node import PocketNode
from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb
from poktbot.utils.decorators import retry
from poktbot.utils.formatting import format_date


class PocketNodeErrors(PocketNode):
    """
    Represents a PocketNode with basic API implementation for retrieving errors.

    Usage example:
    >>> from poktbot.api.node import PocketNodeErrors
    >>> node_errors = PocketNodeErrors("047fe6618553aba4816d948aca98808c3eb1ad38")
    >>> node_errors.update()
    >>> node_errors.errors
    """

    def __init__(self, node_address, api_url=None, chain_ids=None, initial_errors_date=None):
        config = get_config()
        relay_db = get_relaydb("errors")
        self._logger = poktbot_logging.get_logger("PocketNodeAPIErrors")

        # We load start page and initial transactions from the database (if not provided)
        node_db_persistence = relay_db.get(node_address, {})

        if initial_errors_date is None:
            initial_errors_date = node_db_persistence.get("last_error_date",
                                                          pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24))

        api_url = api_url or config.get("SERVER.api_url_errors")

        super().__init__(node_address, api_url)

        self._chain_ids = chain_ids or config.get("SERVER.chain_ids")
        self._errors_df = None

        self._last_error_date = initial_errors_date

        self._logger.info(f"{self} instantiated")

    @property
    def last_error_date(self):
        return self._last_error_date

    @retry(max_attempts=3, attempt_interval=5, on_exception=requests.exceptions.RequestException)
    @retry(max_attempts=3, attempt_interval=5, on_exception=LookupError)
    def _request_errors(self, limit=100, direction=-1, page=1):
        """
        Requests the error to the HTTP api url and returns the JSON.

        :param limit:
            Number of transactions to request.

        :param direction:
            Direction of the transactions (-1 from head or 1 from first)

        :param page:
            Page to fetch. Last page contains fewer elements than transactions_limit.

        :return:
            A JSON object containing all the errors in RAW format.
        """
        data = {
            "operationName": "getNodeErrors",
            "variables": {
                "addresses": [
                    f"{self.address}"
                ],
                "page": page,
                "limit": limit,
                "sort": [
                    {
                        "property": "timestamp",
                        "direction": direction
                    }
                ]
            },
            "query": "query getNodeErrors($page: Int!, $limit: Int!, $addresses: [String!]!, $sort: [SortInput]) {\n  getNodeErrors(page: $page, limit: $limit, addresses: $addresses, sort: $sort) {\n    items {\n      address\n      service_url\n      service_domain\n      method\n      message\n      timestamp\n      elapsedtime\n      blockchain\n      nodepublickey\n      applicationpublickey\n      code\n      bytes\n      __typename\n    }\n    pageInfo {\n      page\n      limit\n      total\n      __typename\n    }\n    __typename\n  }\n}\n"
        }

        self._logger.info(f"{self} Requesting errors to node")
        self._logger.debug(f"{self} Requesting errors {data}")

        response = requests.post(
            self._api_url,
            json=data
        )

        self._logger.debug(
            f"{self} Response status code: {response.status_code}")

        if response.status_code != 200:
            raise LookupError(f"Not 200 status code; error: {response.status_code}")

        result = response.json()

        items_count = len(result.get('data', {}).get('getNodeErrors', {}).get('items', []))

        self._logger.debug(f"{self} Response: {response.status_code}; page: {page}; "
                           f"No. elements retrieved: {items_count}")

        return result

    def _fetch_errors(self):
        """
        Fetches all the errors from the last cached error until the last one.

        This method does not update the last_update attribute of this class. The method `update()` is preferred instead.

        Errors are stored within the object and can be accessed through the property `.errors`.

        This method overrides the .errors dataframe with the last snapshot, which won't include the errors
        from the previous snapshot.
        """
        config = get_config()

        date_format = config["SERVER.api_date_format"]
        limit = config["SERVER.api_page_size"]
        max_pages = config["SERVER.api_max_page_count"]

        page_slice = slice(1,
                           max_pages,
                           1)

        errors_list = []

        page = 1

        for page in range(page_slice.start, page_slice.stop, page_slice.step):
            errors_raw = self._request_errors(limit=limit, page=page)
            errors_items = errors_raw.get("data", {}).get("getNodeErrors", {}).get("items", [])
            new_errors_df = pd.DataFrame([self._build_error_element(err, date_format) for err in errors_items])
            is_last_page = (self._last_error_date > new_errors_df['time']).any()

            new_errors_df = new_errors_df[new_errors_df['time'] > self._last_error_date]

            errors_list.append(new_errors_df)

            if is_last_page:
                break

        errors_df = pd.concat(errors_list, axis=0).sort_values("time").reset_index(drop=True)

        self._logger.debug(f"{self} Found {errors_df.shape[0]} new errors")

        with self._lock:
            self._errors_df = errors_df

            if errors_df.shape[0] > 0:
                self._last_error_date = errors_df["time"].max()

    def _build_error_element(self, error_raw_item, date_format):
        """
        Builds the error element from the error item
        """
        error = {
            "wallet": error_raw_item["address"],
            "service_url": error_raw_item["service_url"],
            "message": error_raw_item["message"],
            "chain_id": self._chain_ids[error_raw_item["blockchain"]],
            "time": pd.to_datetime(error_raw_item["timestamp"], format=date_format)
        }

        return error

    @property
    def errors(self):
        """
        Retrieves the last cached errors from this node instance.
        """
        return self._errors_df

    def update(self):
        """
        Updates the node information from the node API URL.
        """
        super().update()
        self._fetch_errors()

    def __str__(self):
        return f"[poktbot - Node {self.address} (errors); last update: {format_date(self.last_update)}; errors count: {self._errors_df.shape[0] if self._errors_df is not None else 0}]"

    def __repr__(self):
        return str(self)
