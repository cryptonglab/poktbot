from threading import Lock, Thread, Event

from poktbot.api.api import API
from poktbot.log import poktbot_logging

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures


class Observer(API):
    """
    Class that executes updates on a periodic interval.

    After an update, a callback is triggered (on_update). A callback can be set by `set_callback()` method.
    """
    def __init__(self, elements, update_interval, on_update=None, observer_name=None, pool_size=2):
        """
        Constructor of the class.

        In order to start the observer, call `start()` method. This will trigger updates of every contained API element
        on each `update_interval` seconds.

        :param elements:
            List of API objects to observe.

        :param update_interval:
            Time in seconds of the interval to update. This triggers the `update()` method of each of the contained
            elements.

        :param on_update:
            Function callback for the reception of the update notification (after has been updated).

        :param observer_name:
            Name of the observer. Important for logging purposes.

        :param pool_size:
            Size of the internal pool. If there are many elements to be observed, their observation can be parallelized
            in a thread pool.
        """
        super().__init__()

        self._logger = poktbot_logging.get_logger("Observer")

        self._elements = elements
        self._update_interval = float(update_interval)
        self._lock = Lock()
        self._event = Event()

        self._pool = ThreadPoolExecutor(max_workers=pool_size)
        self._thread = None
        self._name = observer_name

        self._initial_observation = True
        self._stop = False
        self._callbacks = []

        if on_update is not None:
            self.set_callback(on_update)

    @property
    def name(self):
        return self._name

    def start(self, initial_observation=True):
        if self._thread is None:
            self._initial_observation = initial_observation
            self._logger.info(f"{self} Starting observer")
            self._stop = False
            self._event.clear()
            self._thread = Thread(target=self._thread_func, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop = True
        self._event.set()

        if self._thread is not None:
            self._thread.join()

        self._thread = None

    def _thread_func(self):
        if self._initial_observation:
            self.update()

        while not self._stop:
            while not self._event.wait(timeout=self._update_interval):
                self.update()

            if not self._stop:
                self.update()
                self._event.clear()

        with self._lock:
            self._thread = None

    def add(self, element):
        with self._lock:
            self._elements.append(element)

    def remove(self, element):
        with self._lock:
            self._elements.remove(element)

    def __len__(self):
        with self._lock:
            return len(self._elements)

    def __iter__(self):
        with self._lock:
            iterator = self._elements.__iter__()

        yield from iterator

    def __getitem__(self, item):
        return self._elements[item]

    def __contains__(self, item):
        return item in self._elements

    def update(self):
        self._logger.debug(f"{self} Update triggered")
        promises = [self._pool.submit(l.update) for l in self._elements]
        concurrent.futures.wait(promises)

        for callback in self._callbacks:
            callback()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"[Observer {self._name}: {len(self._elements)} elements observed]"

    def add_callback(self, new_callback):
        self._callbacks.append(new_callback)

    def remove_callback(self, callback):
        self._callbacks.remove(callback)

    def trigger_update(self):
        """
        Triggers an update of the observer.

        This is a non-locking method.
        """
        self._event.set()
