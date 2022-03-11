from poktbot.config import get_config
from poktbot.telegram.rbac.atomic import Stats

import pkg_resources
import yaml


class Investor(Stats):
    """
    Investor role.

    All the available investor actions are stored as methods of this class.

    The layout stored at "poktbot/layouts/investor.yaml" maps menu entries to those actions by reflection.
    """
    def __init__(self, conv, entity):
        super().__init__(conv, entity)
        self._load_layout()

    def _load_layout(self):
        with open(pkg_resources.resource_filename("poktbot", "telegram/layouts/investor.yaml"), "r") as f:
            self._layout = yaml.safe_load(f)

    def allowed(self):
        config = get_config()

        investors_ids = config.get("IDS.investors_ids", [])
        investors_ids = investors_ids if type(investors_ids) is list else [investors_ids]

        ids_list = [int(i) for i in investors_ids if i != '']
        return self._entity.id in ids_list

    async def menu_main(self, menu=None, **kwargs):
        """
        Displays the main menu to the telegram user and handles its interaction.
        """
        return await self.menu("menu_main", menu_caption="Menu:", relaunch_on_exit=True)
