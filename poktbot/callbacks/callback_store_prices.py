from poktbot.api import get_observer
from poktbot.log import poktbot_logging
from poktbot.storage import get_relaydb


class CallbackStorePrices:
    """
    Callback invoked when the cached prices data should be stored in a database.

    This is usually invoked after all the prices from a price provider is fetched.
    """

    def __init__(self):
        self._logger = poktbot_logging.get_logger("CallbackStorePrices")

    def __call__(self, *args, **kwargs):
        self._logger.debug("Triggered store of prices (if any)")

        observer_prices = get_observer("prices")
        prices_db = get_relaydb("prices")

        # We store the whole prices series. We always keep the whole prices series in memory.
        prices_db["prices"] = observer_prices[0].prices
