import asyncio


def periodic(period):
    """
    Executes an AsyncIO function periodically.
    :param period: time (seconds) of the period to execute the function
    """

    # periodic function
    def scheduler(fcn):
        async def wrapper():
            while 1:
                asyncio.ensure_future(fcn())
                await asyncio.sleep(period)

        return wrapper

    return scheduler
