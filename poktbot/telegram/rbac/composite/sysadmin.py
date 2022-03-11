from poktbot.config import get_config
from poktbot.telegram.rbac.atomic import Balances, Server, Stats, Users, Nodes

import pkg_resources
import yaml


class SysAdmin(Users, Server, Balances, Stats, Nodes):
    """
    SysAdmin role.

    All the available sysadmin actions are stored as methods of this class.

    The layout stored at "poktbot/layouts/sysadmin.yaml" maps menu entries to those actions by reflection.
    """
    def __init__(self, conv, entity):
        super().__init__(conv, entity)
        self._load_layout()

    def _load_layout(self):
        with open(pkg_resources.resource_filename("poktbot", "telegram/layouts/sysadmin.yaml"), "r") as f:
            self._layout = yaml.safe_load(f)

    def allowed(self):
        config = get_config()

        sysadmins_ids = config.get("IDS.sysadmins_ids", [])
        sysadmins_ids = sysadmins_ids if type(sysadmins_ids) is list else [sysadmins_ids]

        ids_list = [int(i) for i in sysadmins_ids if i != '']
        return self._entity.id in ids_list

    async def menu_main(self, menu=None, **kwargs):
        """
        Displays the main menu to the telegram user and handles its interaction.
        """
        return await self.menu("menu_main", menu_caption="Menu:", relaunch_on_exit=True)

    async def menu_users(self, menu=None, **kwargs):
        """
        Displays the users menu to the telegram user and handles its interaction.
        """
        if menu is not None:
            await menu.delete()

        relaunch_menu = True

        while relaunch_menu:
            relaunch_menu = await self.menu("menu_users", menu_caption="Select an option:", relaunch_on_exit=False)

        return True

    async def menu_server(self, menu=None, **kwargs):
        """
        Displays the server menu to the telegram user and handles its interaction.
        """
        if menu is not None:
            await menu.delete()

        relaunch_menu = True

        while relaunch_menu:
            relaunch_menu = await self.menu("menu_server", menu_caption="Select an option:", relaunch_on_exit=False)

        return True

    async def menu_balances(self, menu=None, **kwargs):
        """
        Displays the balances menu to the telegram user and handles its interaction.
        """
        if menu is not None:
            await menu.delete()

        relaunch_menu = True

        while relaunch_menu:
            relaunch_menu = await self.menu("menu_balances", menu_caption="Options:", relaunch_on_exit=False)

        return True

    async def menu_nodes(self, menu=None, **kwargs):
        """
        Displays the nodes menu to the telegram user and handles its interaction.
        """
        if menu is not None:
            await menu.delete()

        relaunch_menu = True

        while relaunch_menu:
            relaunch_menu = await self.menu("menu_nodes", menu_caption="Options:", relaunch_on_exit=False)

        return True
