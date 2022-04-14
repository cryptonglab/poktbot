from poktbot.constants import __version__, __db_version__
from poktbot.telegram.rbac.role import Role


class Info(Role):
    """
    Basic role of information.

    Any telegram role that inherits from this class is able to display information of the system.
    """

    async def show_info(self, menu=None, **kwargs):
        """
        Shows information of the current bot.
        This method is invoked by the interaction of the user with the telegram bot.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv

        try:
            await conv.send_message(f"APP VERSION: {__version__}\n"
                                    f"DB VERSION: {__db_version__}")

        finally:
            await menu.delete()

        return True
