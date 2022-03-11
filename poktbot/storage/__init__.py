from poktbot.config import get_config
from poktbot.storage.local.joblib.relay_db_jl import RelayDBjl

import os


AVAILABLE_RELAYDB_TYPES = {
    "joblib": RelayDBjl,
}


_relay_dbs = {}


def get_relaydb(db_name="transactions"):
    """
    Global singleton for retrieving a relay DB object.

    The first time this function is called, it will try to load the RelayDB and store it in a global scope.
    Rest of the calls return the same RelayDB object.

    As of 20/feb/2022, only a RelayDB based on a JobLIB local file is supported. T

    :return:
        The RelayDB object
    """
    global _relay_dbs
    config = get_config()

    if not db_name.endswith(".db"):
        db_name = f"{db_name}.db"

    _relay_db = _relay_dbs.get(db_name)
    if _relay_db is None:
        relay_db_proto = AVAILABLE_RELAYDB_TYPES[config["SERVER.database_type"]]
        _relay_db = relay_db_proto(os.path.join(config["SERVER.database_secret"], db_name))
        _relay_dbs[db_name] = _relay_db

    return _relay_db


__all__ = ["get_relaydb"]
