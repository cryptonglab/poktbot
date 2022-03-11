from threading import Lock

from poktbot.api.api import API


class PocketNode(API):
    """
    Represents a PocketNode with basic API implementation. This is an abstract class.
    """

    def __init__(self, node_address, api_url):
        super().__init__()
        self._api_url = api_url
        self._address = node_address
        self._lock = Lock()

    @property
    def address(self):
        return self._address

    @property
    def api_url(self):
        return self._api_url

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        raise NotImplementedError()
