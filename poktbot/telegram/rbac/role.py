import asyncio
from threading import Lock

from poktbot.log import poktbot_logging
from poktbot.telegram.exceptions.rbac_error import RBACError
from poktbot.utils.telegram import build_layout

from telethon import events


class Role:

    def __init__(self, conv, entity):
        self._conv = conv
        self._entity = entity
        self._layout = {}
        self._lock = Lock()
        self._logger = poktbot_logging.get_logger("Role")

    def _load_layout(self):
        self._layout = {}

    def allowed(self):
        return False

    async def _check_preconditions(self, menu, menu_required=True, **kwargs):
        """
        Checks whether the preconditions that should be met are actually met before executing any
        action. This implies checking if the user is allowed to perform the operation.
        """
        conv = self._conv

        if not self.allowed():
            await conv.send_message(f"Not allowed")
            raise RBACError(f"{self.id} not allowed")

        if menu is None and menu_required:
            # Security measure: this action cannot be launched without a menu interaction.
            await conv.send_message(f"Not allowed")
            raise RBACError(f"{self.id} not allowed")

    @property
    def id(self):
        return self._entity.id

    async def menu(self, menu_name, menu_caption="Menu:", relaunch_on_exit=True):
        """
        Displays the specified menu to the user conversation.

        :param menu_name:
            Name of the menu defined in the layout. The layout is automatically loaded by the `_load_layout()` method.
            If a layout does not contain the specified menu name, an error is displayed.

        :param menu_caption:
            Caption to display for the menu shown in telegram.

        :param relaunch_on_exit:
            Boolean flag that tells the parent caller to relaunch the menu in a loop. This flag is returned by this
            method. Useful to keep a menu in a loop without filling the function calling stack.

        :return:
            True if menu should be relaunched on return. False otherwise.
        """
        conv = self._conv
        menu_handler = None
        self._logger.debug(f"Building menu {menu_name} with caption '{menu_caption}' for user {self.id}...")

        try:

            if not self.allowed():
                await conv.send_message(message="Not allowed")
                self._logger.warning(f"Building menu {menu_name} for user {self.id}: Failed. Not allowed")
                raise RBACError("Not allowed")

            layout = self._layout.get(menu_name)

            if layout is None:
                await conv.send_message(message="Menu not available")
                self._logger.warning(f"Building menu {menu_name} for user {self.id}: Failed. Not available")
                raise RBACError("Menu not available")

            menu_layout, menu_actions = build_layout(layout)
            self._logger.debug(f"Building menu {menu_name} for user {self.id}: Layout is {menu_layout} with actions {menu_actions}")

            menu_handler = await self._conv.send_message(message=menu_caption, buttons=menu_layout)
            inline_press = await self._conv.wait_event(events.CallbackQuery(self.id))

            selection = inline_press.data.decode("utf-8")
            self._logger.info(f"Client {self.id} selected option {selection}")

            # Now we seek for the action given the selection
            option_correct = False

            for action in menu_actions:
                if action in selection:
                    # A little reflection here: we invoke the method
                    reflected_method_name = menu_actions[action]

                    if hasattr(self, reflected_method_name):
                        self._logger.info(f"Client {self.id} successfully entered at option {selection}")
                        reflected_method = getattr(self, reflected_method_name)

                        try:
                            # If the calling method returns False, the menu is not relaunched.
                            self._logger.debug(f"Client {self.id} invoked action {reflected_method_name}")
                            should_relaunch = await reflected_method(menu_handler)

                            relaunch_on_exit = relaunch_on_exit and should_relaunch
                        except Exception as e:
                            self._logger.error(f"Client {self.id} invoked action {reflected_method_name} with error: {str(e)}")

                        self._logger.debug(f"Client {self.id} action {reflected_method_name} finished")

                        option_correct = True
                        break

                    else:
                        self._logger.error(f"Client {self.id} attempted the option {selection} not available in role")
                        raise RBACError(f"Client {self.id} attempted the option {selection} not available in role. Check the layout definition")

            if not option_correct:
                self._logger.error(f"Client {self.id} selected an incorrect option {selection}")
                raise RBACError(f"Client {self.id} selected an incorrect option {selection}")

        except asyncio.TimeoutError as e:
            self._logger.info(f"Client {self.id} timedout for menu {menu_name}. Disabling relaunch")
            relaunch_on_exit = False

        finally:
            if menu_handler is not None:
                await menu_handler.delete()

        return relaunch_on_exit
