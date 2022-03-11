from time import sleep


def retry(max_attempts=3, attempt_interval=None, on_exception=None, raise_last=True):
    """
    Decorator for methods that allows to retry its execution when a given exception is raised.

    :param max_attempts:
        Number of attempts to try to execute the method before giving up.

    :param attempt_interval:
        Float number of seconds to wait between attempts. None for no wait time.

    :param on_exception:
        Exception to capture and use to try. None to capture any exception

    :param raise_last:
        Flag to determine if should we raise the exception or not in the last attempt if it fails.

    :returns:
        Result of the decorated method.
    """
    if on_exception is None:
        on_exception = Exception

    def decorator(func):

        def pre_execution(self, *args, **kwargs):

            attempts = 0
            success = False
            result = None
            last_exception = None

            while attempts < max_attempts and not success:
                attempts += 1

                try:
                    result = func(self, *args, **kwargs)
                    success = True
                except on_exception as e:
                    last_exception = e

                    if hasattr(self, "_logger"):
                        self._logger.warning(
                            f"Exception {str(e)} executing {func.__name__}, attempt {attempts}/{max_attempts}")

                    if attempt_interval is not None:
                        sleep(attempt_interval)

            if not success:
                if hasattr(self, "_logger"):
                    self._logger.error(f"Exception {str(last_exception)} executing {func.__name__}. Giving up.")

                if raise_last and last_exception is not None:
                    raise last_exception

            return result

        return pre_execution

    return decorator
