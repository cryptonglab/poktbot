from threading import Thread, Lock

from telethon import TelegramClient, events

from poktbot.config import get_config
from poktbot.log import poktbot_logging
from poktbot.telegram.rbac import get_roles

import asyncio
import os


if hasattr(asyncio, "exceptions"):
    ASYNCIO_TIMEOUT_ERROR = asyncio.exceptions.TimeoutError
else:
    ASYNCIO_TIMEOUT_ERROR = asyncio.TimeoutError


class TelegramBot:
    """
    Representation of the telegram bot poktbot.

    This class wraps a thread that handles the asynchronous communication with the users through Telegram.

    Usage example:

    >>> from poktbot.telegram import TelegramBot
    >>> bot = TelegramBot()
    >>> bot.start()
    >>> bot.join()

    """
    def __init__(self, api_id=None, api_hash=None, bot_token=None, session_path=None, session_name=None):

        config = get_config()

        self._session_path = config['TELEGRAM_API.session_path'] if session_path is None else session_path
        self._session_name = config['TELEGRAM_API.session_name'] if session_name is None else session_name
        self._api_hash = config['TELEGRAM_API.api_hash'] if api_hash is None else api_hash
        self._api_id = config['TELEGRAM_API.api_id'] if api_id is None else api_id
        self._bot_token = config["TELEGRAM_API.bot_token"] if bot_token is None else bot_token
        self._telethon_bot = None

        self._global_timeout = int(config["CONF.global_timeout"])
        self._global_periodic_time = int(config["CONF.global_periodic_time"])

        self._logger = poktbot_logging.get_logger("TelegramBot")
        self._thread = None
        self._lock = Lock()
        self._messages_queue = []

        self._loop = None
        self._event = None
        self._bot = None

    @property
    def session_fqpath(self):
        return os.path.join(self._session_path, self._session_name)

    def send_message(self, entity, message):
        with self._lock:
            self._messages_queue.append((entity, message))

    def start(self):
        self._logger.info("Telegram bot started")
        self._exit = False
        self._thread = Thread(target=self._thread_func, daemon=True)
        self._thread.start()

    def join(self, timeout=None):
        self._thread.join(timeout=timeout)

    def stop(self):
        if self._thread is not None and self._event is not None:
            self._logger.info("Telegram bot stopped")
            self._event.set()
            self._thread.join()

    def _thread_func(self):
        self._loop = asyncio.new_event_loop()
        self._event = asyncio.Event(loop=self._loop)
        self._logger.info(f"Starting telegram session on {self.session_fqpath}")
        os.makedirs(self._session_path, exist_ok=True)

        self._telethon_bot = TelegramClient(self.session_fqpath, self._api_id, self._api_hash, loop=self._loop).start(bot_token=self._bot_token)
        self._bot = self._telethon_bot

        bot = self._bot

        async def bot_manager():
            """
            All listeners from Telegram client go here.
            """
            @bot.on(events.NewMessage(pattern="/start", incoming=True))
            async def _start(event):
                """
                This function is triggered on a conversation start with the bot (or the message /start)
                """
                entity = await event.client.get_entity(event.from_id)
                self._logger.debug(f"Request for start (Entity: {entity})")

                # We get the RBAC representation for the entity
                async with bot.conversation(entity.id, timeout=self._global_timeout) as conv:
                    self._logger.debug(f"Conv started")

                    entity_roles = get_roles(entity, conv)
                    self._logger.debug(f"Roles fetched: {entity_roles}")

                    message = f"Welcome {entity.first_name}" if len(entity_roles) > 0 else "Not allowed"
                    self._logger.debug(f"Sent message: {message}")
                    await conv.send_message(message=message)

            @bot.on(events.NewMessage(pattern="/menu", incoming=True))
            async def _menu(event):
                """
                This function is triggered on a message /menu detected
                """
                entity = await event.client.get_entity(event.from_id)

                # We ensure that there's no conversation opened already
                # Fixes issue with client not able to reset his /menu
                async with bot.conversation(entity.id, timeout=self._global_timeout, exclusive=False) as conv:
                    await conv.cancel_all()

                # We get the RBAC representation for the entity
                async with bot.conversation(entity.id, timeout=self._global_timeout, exclusive=False) as conv:
                    entity_roles = get_roles(entity, conv)

                    # if there are roles for the user, we pick the first of them as representative
                    if len(entity_roles) > 0:
                        role = entity_roles[0]
                        self._logger.info(f"Request for menu for user {entity.id} detected rol: {role}")

                        launch_menu = True

                        while launch_menu:
                            launch_menu = await role.menu_main()
                    else:
                        self._logger.warning(f"Request for menu for user {entity.id} without detected rol. Not allowed")
                        await conv.send_message(message="Not allowed")

        async def main_loop():
            """
            Main loop of the asyncio task.

            It wraps the execution of the bot but checking every second if an exit was requested first.
            If bot.stop() is requested, this loop will be notified and finished, hence closing the bot.
            """
            await bot_manager()

            finish = False

            while not finish:
                try:
                    await asyncio.wait_for(self._event.wait(), timeout=1)
                    finish = True

                except ASYNCIO_TIMEOUT_ERROR:
                    with self._lock:
                        messages = list(self._messages_queue)
                        self._messages_queue.clear()

                    for entity, message in messages:
                        self._logger.info(f"Sending message \"{message[:100]}\" (truncated to 100 chars) to entity {entity}")
                        await bot.send_message(entity, message)

            await bot.disconnect()

        # We create a future of the bot_manager
        self._loop.run_until_complete(main_loop())
        # If code reaches this line, the thread is finishing.
        self._thread = None
