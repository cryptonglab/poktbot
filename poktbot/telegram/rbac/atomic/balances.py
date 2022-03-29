from io import BytesIO

from poktbot.api import get_observer
from poktbot.config import get_config
from poktbot.storage import get_relaydb
from poktbot.telegram.rbac.role import Role

import pandas as pd

from poktbot.utils.formatting import format_date, df_to_xlsx


class Balances(Role):

    """
    Basic role of balances management.

    Any telegram role that inherits from this class is able to manage download balances in several
    formats.
    """
    async def send_csv(self, menu=None, **kwargs):
        """
        Builds the CSV file of balances and sends it through the telegram chat.

        :param menu:
            Menu that invoked this action.
        """
        self._logger.debug("Sending CSV to user")

        await self._check_preconditions(menu, **kwargs)
        conv = self._conv

        balances_df = await self._generate_balances_df()

        if menu is not None:
            await menu.delete()

        with BytesIO() as b:
            balances_df.to_csv(b)
            b.seek(0)
            b.name = "balances.csv"
            await conv.send_file(b)

        return False

    async def send_xlsx(self, menu=None, **kwargs):
        """
        Builds the XLSX file of balances and sends it through the telegram chat.

        :param menu:
            Menu that invoked this action.
        """
        self._logger.debug("Sending XLSX to user")

        await self._check_preconditions(menu, **kwargs)
        conv = self._conv

        balances_df = await self._generate_balances_df()

        if menu is not None:
            await menu.delete()

        with BytesIO() as b:
            df_to_xlsx(balances_df, b, sheet_name="Balances")
            b.seek(0)
            b.name = "balances.xlsx"
            await conv.send_file(b)

        return False

    async def _generate_balances_df(self):
        """
        Generates the balances dataframe
        """
        relay_db = get_relaydb("transactions")
        config = get_config()
        nodes_observer = get_observer("nodes_transactions")

        currency = config["PRICE.currency"]
        currency_alias = config["PRICE.currency_alias"]

        columns = ["Type", "Buy Amount", "Buy Cur.", "Sell Amount", "Sell Cur.", "Fee Amount (optional)",
                   "Fee Cur. (optional)", "Exchange (optional)", "Trade Group (optional)", "Comment (optional)",
                   "Date", "Tx-ID", f"Buy Amount {currency_alias}", "Wallet", "Chain_id", "Confirmed"]
        content = []

        # We only make stats for nodes available in the DB
        nodes_addresses = [node.address for node in nodes_observer if node.address in relay_db]

        for node_address in nodes_addresses:
            transactions_df = relay_db.get(node_address, {}).get("transactions")

            if transactions_df is None:
                continue

            for row_index, row_content in transactions_df.iterrows():
                if "claim" in row_content["type"]:
                    content_element = [
                        "Minning",
                        str(row_content["amount"]).replace(".", ","),
                        "POKT", "", "", "", "", "Pocket", "", "",
                        format_date(row_content["time"]),
                        row_content["hash"],
                        str(row_content[f"amount_price_{currency}"]).replace(".", ","),
                        row_content["wallet"],
                        row_content["chain_id"],
                        row_content["confirmed"],
                    ]

                    content.append(content_element)

        balances_df = pd.DataFrame(content, columns=columns)

        return balances_df
