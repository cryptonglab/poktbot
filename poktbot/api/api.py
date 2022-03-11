import pandas as pd


class API:
    def __init__(self):
        self._last_update = None

    def update(self):
        self._last_update = pd.Timestamp.now("UTC")

    @property
    def last_update(self):
        return self._last_update
