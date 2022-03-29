import logging
import os


DEFAULT_LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", "INFO")


class Logging:
    """
    Singleton for logging.

    This eases the retrieval of loggers with a uniform format for all the library.
    """

    def __init__(self, level=DEFAULT_LOGGING_LEVEL):
        self._level = level
        self._handlers = [logging.StreamHandler()]
        self._formatter = logging.Formatter('[%(levelname)-2s %(threadName)s] %(asctime)s - %(name)s - %(message)s ')
        self._loggers = {}

        for handler in self._handlers:
            handler.setFormatter(self._formatter)
            handler.setLevel(self._level)

    def get_logger(self, logger_name):
        logger = self._loggers.get(logger_name)

        if logger is None:
            logger = logging.getLogger(logger_name)
            logger.setLevel(self._level)

            for handler in self._handlers:
                logger.addHandler(handler)

        self._loggers[logger_name] = logger
        return logger

    def set_level(self, new_level):
        for handler in self._handlers:
            handler.setLevel(new_level)

        for logger in self._loggers.values():
            logger.setLevel(new_level)

    def add_file_handler(self, filename):
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(self._level)
        file_handler.setFormatter(self._formatter)
        self._handlers.append(file_handler)

        for logger in self._loggers.values():
            logger.addHandler(file_handler)


poktbot_logging = Logging()
