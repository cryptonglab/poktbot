from poktbot.telegram.rbac.role import Role


class Server(Role):
    """
    Basic role of server management.

    Any telegram role that inherits from this class is able to manage the start/stop and check of the system.
    """

    async def turn_on_server(self, menu=None, **kwargs):
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        await conv.send_message(message="Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    async def turn_off_server(self, menu=None, **kwargs):
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        await conv.send_message(message="Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    async def server_status(self, menu=None, **kwargs):
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        await conv.send_message(message="Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    async def home(self, menu=None, **kwargs):
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        await menu.delete()
        await self.menu("menu_main")

