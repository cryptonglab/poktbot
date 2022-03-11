import asyncio

from telethon import Button, events

from poktbot.config import get_config
from poktbot.telegram.exceptions.rbac_error import RBACError
from poktbot.telegram.rbac.role import Role


class Users(Role):
    """
    Basic role of users management.

    Any telegram role that inherits from this class is able to manage creation/deletion of admins
    or investors to the system.
    """

    async def add_admin(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to add new admins.
        This method is invoked by the interaction of the user with the telegram bot.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        config = get_config()

        try:
            await conv.send_message("Which user?")

            response = await conv.get_response()
            member_id = response.message

            # If replied with a command, we abort the method.
            if member_id.startswith("/"):
                return True

            # If replied with not an ID, we abort the method
            try:
                member_id = int(member_id)
            except ValueError:
                return True

            if member_id in config['IDS.admins_ids']:
                self._logger.info(f"Client {self.id} tried to add {member_id} as Admin, but {member_id} already configured as Admin")
                await conv.send_message(f"User {member_id} already configured as an Admin")
                raise RBACError(f"User {member_id} already configured as an Admin")

            with self._lock:
                ids = config['IDS.admins_ids']
                ids = [int(i) for i in (ids if type(ids) is list else [ids]) if i != '']
                ids.append(member_id)

                config['IDS.admins_ids'] = ids

            self._logger.info(f"Client {self.id} added {member_id} as Admin")
            await conv.send_message(f"User added as admin: {member_id}")

            config.save()

        finally:
            await menu.delete()

        return True

    async def add_investor(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to add new investors.
        This method is invoked by the interaction of the user with the telegram bot.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        config = get_config()

        try:
            await conv.send_message("Which user?")

            response = await conv.get_response()
            member_id = response.message

            # If replied with a command, we abort the method.
            if member_id.startswith("/"):
                return True

            # If replied with not an ID, we abort the method
            try:
                member_id = int(member_id)
            except ValueError:
                return True

            if member_id in config['IDS.investors_ids']:
                self._logger.info(f"Client {self.id} tried to add {member_id} as Investor, but {member_id} already configured as Investor")
                await conv.send_message(f"User {member_id} already configured as an Investor")
                raise RBACError(f"User {member_id} already configured as an Investor")

            with self._lock:
                ids = config['IDS.investors_ids']
                ids = [int(i) for i in (ids if type(ids) is list else [ids]) if i != '']
                ids.append(member_id)

                config['IDS.investors_ids'] = ids

            config.save()

            self._logger.info(f"Client {self.id} added {member_id} as Investor")
            await conv.send_message(f"User added as investor: {member_id}")

        finally:
            await menu.delete()

        return True

    async def delete_admin(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to remove admins.
        This method is invoked by the interaction of the user with the telegram bot.

        A menu listing existing admins will be shown. The user must tap one of the elements
        in order to select the admin to be deleted.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        config = get_config()

        # Here we build the markup for each investor so the user can select
        markup = [[Button.inline(str(member_id))] for member_id in config['IDS.admins_ids']]
        menu_ids = await conv.send_message(message="Select ID to delete: \n", buttons=markup)

        try:
            inline_press = await conv.wait_event(events.CallbackQuery(self.id))
            member_id = inline_press.data.decode("UTF-8")

            with self._lock:
                ids = config['IDS.admins_ids']
                ids = [int(i) for i in (ids if type(ids) is list else [ids]) if i != '']
                ids.remove(member_id)

                config['IDS.admins_ids'] = ids

            self._logger.info(f"Client {self.id} removed {member_id} from Admin")

        except asyncio.TimeoutError as e:
            await conv.send_message(message="Selection timed out")

        except ValueError as e:
            await conv.send_message(message="Selected member doesn't exist")

        finally:
            await menu_ids.delete()

        return True

    async def delete_investor(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to remove investors.
        This method is invoked by the interaction of the user with the telegram bot.

        A menu listing existing investors will be shown. The user must tap one of the elements
        in order to select the investor to be deleted.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        config = get_config()

        # Here we build the markup for each investor so the user can select
        markup = [[Button.inline(str(member_id))] for member_id in config['IDS.investors_ids']]
        menu_ids = await conv.send_message(message="Select ID to delete: \n", buttons=markup)

        try:
            inline_press = await conv.wait_event(events.CallbackQuery(self.id))
            member_id = inline_press.data.decode("UTF-8")

            with self._lock:
                ids = config['IDS.investors_ids']
                ids = [int(i) for i in (ids if type(ids) is list else [ids]) if i != '']
                ids.remove(member_id)

                config['IDS.investors_ids'] = ids

            self._logger.info(f"Client {self.id} removed {member_id} from Investor")

        except asyncio.TimeoutError as e:
            await conv.send_message(message="Selection timed out")

        except ValueError as e:
            await conv.send_message(message="Selected member doesn't exist")

        finally:
            await menu_ids.delete()

        return True
