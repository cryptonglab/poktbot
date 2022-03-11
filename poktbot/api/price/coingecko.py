from poktbot.api.api import API
from poktbot.config import get_config

import requests
import pandas as pd

from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb
from poktbot.utils.decorators import retry
from poktbot.utils.formatting import format_date

HOUR = 3600 * 1000


class Coingecko(API):
    """
    Fetches prices from Coingecko for a given cryptocurrency.
    Usage example:

        >>> coingecko = Coingecko()
        >>> coingecko.fetch_prices(start="2022-01-01", cryptocurrency="pocket-network")
                          prices   market_caps  total_volumes
        date_timestamp
        1641993158731   1.745302  0.000000e+00   2.341358e+06
        1641996122549   1.706441  0.000000e+00   2.635731e+06
        1642000676526   1.689737  0.000000e+00   3.327124e+06
        1642003249519   1.735076  0.000000e+00   3.515893e+06
        1642007010749   1.906108  0.000000e+00   4.485270e+06
        ...                  ...           ...            ...
        1644426011856   1.193809  8.801675e+08   4.105306e+06
        1644429795981   1.193035  8.795690e+08   4.196542e+06
        1644433391878   1.194355  8.806017e+08   4.188826e+06
        1644436947936   1.192538  8.786998e+08   4.181573e+06
        1644440520522   1.193196  8.795960e+08   4.158033e+06

        [680 rows x 3 columns]
    """

    def __init__(self, api_url=None, start_date=None):
        super().__init__()
        config = get_config()
        prices_db = get_relaydb("prices")

        self._logger = poktbot_logging.get_logger("CoingeckoAPI")
        self._api_url = api_url or config['PRICE.coingecko_url']

        self._prices = prices_db.get("prices", None)
        self._start_date = int(self._prices.index.max())+1000 if self._prices is not None else start_date
        self._logger.debug(f"Loaded {self._prices.shape[0] if self._prices is not None else 0} prices from DB.")

    @property
    def start_date(self):
        return self._start_date

    @retry(attempt_interval=0.5)
    def fetch_prices(self, start=None, end=None, cryptocurrency="pocket-network", currency=None, index_as_dates=False):
        """
        Fetches the prices between the specified range.

        :param start:
            Start of the range to fetch the price.

        :param end:
            End of the range to fetch the price.
            If no end is defined, the price is returned until today (now).

        :param cryptocurrency:
            Name of the cryptocurrency to retrieve data from. Default is "pocket-network".

        :param currency:
            Name of the currency. By default, it is loaded from config param PRICE.currency.
            Expected values: eur, usd, ...

        :param index_as_dates:
            Boolean flag indicating if the output should have dates as datetime objects (True) or as timestamps (False).

        :returns:
            A pd.Dataframe containing:
               - 3 columns: prices, market_caps and total_volumes
               - 1 index: date_timestamp
        """
        config = get_config()

        if type(end) is str:
            end = pd.to_datetime(end)
        elif type(end) in [int, float]:
            end = pd.to_datetime(end / 1000, unit="s")
        elif end is None:
            end = pd.Timestamp.utcnow()

        if type(start) is str:
            start = pd.to_datetime(start)
        elif type(start) in [int, float]:
            start = pd.to_datetime(start / 1000, unit="s")
        elif start is None:
            start = self._start_date if self._start_date is not None else end - pd.DateOffset(months=1)

            if type(start) in [int, float]:
                start = pd.to_datetime(start / 1000, unit="s")

        if currency is None:
            currency = config.get("PRICE.currency", "eur")

        url = self._api_url.format(cryptocurrency=cryptocurrency,
                                   currency=currency,
                                   start=int(start.timestamp()),
                                   end=int(end.timestamp()))

        self._logger.info(f"{self} Requesting prices from {start} to {end} in currency {currency}")
        self._logger.debug(f"{self} Requesting to url {url}")

        response = requests.get(url)

        self._logger.debug(f"{self} Response: {response.status_code}; text: {response.text[:100]} (truncated to 100 characters)")

        if response.status_code != 200:
            raise LookupError(f"Not 200 status code; error: {response.status_code}; text: {response.text}")

        prices_df = pd.concat(
            [pd.DataFrame(value, columns=["date_timestamp", key]).set_index("date_timestamp")
             for key, value in response.json().items()], axis=1)

        if index_as_dates:
            prices_df.index = pd.DatetimeIndex(pd.to_datetime(prices_df.index / 1000, unit="s"),
                                               name=prices_df.index.name)

        return prices_df

    @property
    def prices(self):
        return self._prices

    def update(self):
        super().update()

        new_prices = self.fetch_prices(start=self.start_date if self.start_date is not None else "2022-01-01")
        self._logger.info(f"Retrieved {new_prices.shape[0] if new_prices is not None else 0} new prices from API.")
        self._prices = pd.concat([self._prices, new_prices], axis=0) if new_prices is not None else new_prices

        max_date = self.prices.index.max()

        if pd.isna(max_date):
            max_date = self._start_date
        else:
            max_date = int(max_date) + 1000

        self._start_date = max_date

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"[poktbot - Coingecko; last update: {format_date(self.last_update)}]"
