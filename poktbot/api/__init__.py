from poktbot.api.observer import Observer
from poktbot.config import get_config

_OBSERVERS = {}


def get_observer(observer_name, update_interval=None):
    """
    Singleton for observers.

    An observer is an object that updates its children asynchronously each `update_interval` and that triggers a
    callback. Every children appended to the observer must implement the `poktbot.api.API` class, or contain a
    `update()` method.

    :param observer_name:
        Name of the observer singleton to fetch. If exists, retrieves the same observer every call.
        If it doesn't exist, the method creates it.

    :param update_interval:
        Interval in seconds for the observer to update. If not provided, by default it will load the
        update interval defined by the config file parameter `CONF.global_periodic_time`.

    :returns:
        Observer of the given name.
    """
    obs = _OBSERVERS.get(observer_name)

    if obs is None:
        config = get_config()

        if update_interval is None:
            update_interval = config['CONF.global_periodic_time']

        obs = Observer([], update_interval=update_interval, observer_name=observer_name)
        _OBSERVERS[observer_name] = obs

    return obs


__all__ = ["get_observer", "Observer"]
