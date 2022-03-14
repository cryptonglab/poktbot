import asyncio

from telethon import Button, events

from poktbot.api import get_observer
from poktbot.api.node import PocketNodeTransactions, PocketNodeErrors
from poktbot.config import get_config
from poktbot.telegram.exceptions.rbac_error import RBACError
from poktbot.telegram.rbac.role import Role


class Nodes(Role):
    """
    Basic role of users management.

    Any telegram role that inherits from this class is able to manage tracking of nodes of the system
    """

    async def add_node(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to add new nodes.
        This method is invoked by the interaction of the user with the telegram bot.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        config = get_config()

        try:
            await conv.send_message("Which node address?")

            response = await conv.get_response()
            node_address = response.message

            # If replied with a command, we abort the method.
            if node_address.startswith("/"):
                return True

            nodes_list = config['SERVER.nodes']
            nodes_list = nodes_list if type(nodes_list) is list else [nodes_list]

            if node_address in nodes_list:
                self._logger.info(f"Client {self.id} tried to add {node_address}, but {node_address} already configured")
                await conv.send_message(f"Node {node_address} already configured")
                raise RBACError(f"Node {node_address} already configured")

            with self._lock:
                # Update the configuration so that new node is taken into account
                nodes_list.append(node_address)
                config['SERVER.nodes'] = nodes_list
                config.save()

            # Update the observer so that next observer update takes this node info
            observer_nodes_transactions = get_observer("nodes_transactions")
            observer_nodes_errors = get_observer("nodes_errors")
            observer_main = get_observer("main")

            observer_nodes_transactions.add(PocketNodeTransactions(node_address=node_address))
            observer_nodes_errors.add(PocketNodeErrors(node_address=node_address))

            self._logger.info(f"Client {self.id} added {node_address} to the system")
            await conv.send_message(f"Node added to the system: {node_address}")

            # We force an update in case.
            observer_main.trigger_update()

        finally:
            await menu.delete()

        return True

    async def delete_node(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to remove nodes.
        This method is invoked by the interaction of the user with the telegram bot.

        A menu listing existing nodes will be shown. The user must tap one of the elements
        in order to select the node to be deleted.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv
        config = get_config()

        # Here we build the markup for each investor so the user can select
        markup = [[Button.inline(str(node_address))] for node_address in config['SERVER.nodes']]
        menu_ids = await conv.send_message(message="Select ID to delete: \n", buttons=markup)

        try:
            inline_press = await conv.wait_event(events.CallbackQuery(self.id))
            node_address = inline_press.data.decode("UTF-8")

            # Update the configuration so that node is no longer taken into account
            with self._lock:
                nodes_list = config['SERVER.nodes']
                nodes_list = nodes_list if type(nodes_list) is list else [nodes_list]
                nodes_list.remove(node_address)
                config['SERVER.nodes'] = nodes_list
                config.save()

            # Update the observer so that next observer update doesn't take this node info
            observer_nodes_transactions = get_observer("nodes_transactions")
            observer_nodes_errors = get_observer("nodes_errors")

            observer_nodes_transactions.add(PocketNodeTransactions(node_address=node_address))
            observer_nodes_errors.add(PocketNodeErrors(node_address=node_address))

            for node in observer_nodes_transactions:
                if node.address == node_address:
                    observer_nodes_transactions.remove(node)
                    break

            for node in observer_nodes_errors:
                if node.address == node_address:
                    observer_nodes_errors.remove(node)
                    break

            self._logger.info(f"Client {self.id} removed node {node_address} from the system")

        except asyncio.TimeoutError as e:
            await conv.send_message(message="Selection timed out")

        except ValueError as e:
            await conv.send_message(message="Selected node doesn't exist")

        finally:
            await menu_ids.delete()

        return True

    async def list_nodes(self, menu=None, **kwargs):
        """
        Handles interaction through conversation to list current tracked nodes.
        This method is invoked by the interaction of the user with the telegram bot.

        A menu listing existing nodes will be shown -- with staking information.

        :param menu:
            menu that was used to launch this action.
        """
        await self._check_preconditions(menu, **kwargs)
        conv = self._conv

        TICKS = {
            True: "✔️",
            False: "❌"
        }

        observer_nodes_transactions = get_observer("nodes_transactions")

        message = [f"{TICKS[node.in_staking]} {node.address}" for node in observer_nodes_transactions]

        await conv.send_message("\n".join(message))
        return True
