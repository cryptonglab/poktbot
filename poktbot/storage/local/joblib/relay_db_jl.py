import os.path
from contextlib import contextmanager

from poktbot.log import poktbot_logging
from poktbot.storage.relay_db import RelayDB

from timeit import default_timer as timer
from datetime import timedelta

import joblib


class RelayDBjl(RelayDB):
    """
    RelayDB using the JobLib backend.

    JobLib allows storing data using several compression methods and levels.
    """
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = poktbot_logging.get_logger("RelayDB-JobLib")
        self._filename = filename
        self._synchronize = True

        if len(args) + len(kwargs) == 0:
            self.load()

    def dump(self):
        """
        Dumps the contents of this DB into the JobLib file
        """
        start = timer()
        with self._lock:
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)
            joblib.dump(dict(self), self._filename, compress=("lz4", 1))
        end = timer()
        self._logger.info(f"Dumped database to {self._filename} ({timedelta(seconds=end - start)} s)")

    def load(self):
        """
        Loads the content from the DB
        """
        start = timer()
        self.clear()

        try:
            with self._lock:
                self.update(joblib.load(self._filename))
        except FileNotFoundError:
            self._logger.warning("Could not load the database, file doesn't exist. Is it a new instance?")

        end = timer()
        self._logger.info(f"Loaded database from {self._filename} ({timedelta(seconds=end - start)} s)")

    def __setitem__(self, key, value):
        super(RelayDBjl, self).__setitem__(key, value)
        if self._synchronize:
            self.dump()

    @contextmanager
    def bulk_op(self):
        """
        Yields an object that allows to make several operations at once before dumping.

        Do not dump/load inside a bulk operation!
        """
        aux_rdb = RelayDBjl(self._filename, self)
        aux_rdb._synchronize = False

        with self._lock:
            yield aux_rdb
            self.update(aux_rdb)

        aux_rdb.dump()
