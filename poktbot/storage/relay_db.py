from threading import Lock


class RelayDB(dict):
    """
    Stores the database in a storage.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = Lock()

    def dump(self):
        """
        Dumps the contents of this DB
        """
        raise NotImplementedError()

    def load(self):
        """
        Loads the content from the DB
        """
        raise NotImplementedError()

    def bulk_op(self):
        """
        Yields an object that allows to make several operations at once before dumping.
        """
        raise NotImplementedError()
