from poktbot.api import get_observer
from poktbot.storage import get_relaydb
from poktbot.config import get_config
from poktbot.telegram.rbac.role import Role

import io
import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('AGG')


class Stats(Role):
    """
    Basic role of stats display.

    Any telegram role that inherits from this class is able to view transactions stats.
    """

    async def menu_stats(self, menu=None, **kwargs):
        """
        Shows the transaction statistics through the conversation.
        This method is invoked by the interaction of the user with the telegram bot.

        :param menu: menu that invoked this action.
        """

        await self._check_preconditions(menu, **kwargs)
        conv = self._conv

        relay_db = get_relaydb("transactions")
        nodes_observer = get_observer("nodes_transactions")
        config = get_config()

        # We only make stats for nodes available in the DB
        nodes_addresses = [node.address for node in nodes_observer if node.address in relay_db]

        total_amounts_df, total_amounts_eur_df = self._compute_all_nodes_totals_df(nodes_addresses=nodes_addresses)

        avg_pocket_rewards_df, \
        avg_pocket_rewards_eur_df, \
        total_pocket_rewards_df, \
        total_pocket_rewards_eur_df = self._generate_rewards_stats_df(total_amounts_df=total_amounts_df,
                                                                      total_amounts_eur_df=total_amounts_eur_df)

        rewards_graph_bytes = self._generate_avg_rewards_graph(total_amounts_df)

        currency_symbol = config.get("PRICE.currency", "eur").upper()

        message = f"📈 Stats:\n" \
                  f"\t\t\t\t**{avg_pocket_rewards_df.iloc[1]} POKTs today (avg).**\n" \
                  f"\t\t\t\t{avg_pocket_rewards_eur_df.iloc[1]} {currency_symbol}s today (avg).\n" \
                  f"\t\t\t\t{avg_pocket_rewards_df.iloc[0]} POKTs everyday (avg).\n" \
                  f"\t\t\t\t{avg_pocket_rewards_eur_df.iloc[0]} {currency_symbol}s everyday (avg).\n" \
                  f"\t\t\t\t{avg_pocket_rewards_df.iloc[3]} POKTs this month (avg).\n" \
                  f"\t\t\t\t{avg_pocket_rewards_eur_df.iloc[3]} {currency_symbol}s this month (avg).\n" \

        await conv.send_message(message=message)
        
        await conv.send_file(rewards_graph_bytes)

        await menu.delete()
        return True

    @staticmethod
    def _compute_amount_totals(node_address):
        config = get_config()
        currency = config.get("PRICE.currency", "eur")
        relay_db = get_relaydb("transactions")

        transactions = relay_db[node_address]['transactions']
        proof_transactions = transactions[transactions['type'].str.contains('claim')]

        # 1. We compute the daily staking mask
        cleaned_transactions = transactions.drop_duplicates("time").set_index("time")
        reindexed_transactions = cleaned_transactions.reindex(pd.date_range(transactions['time'].min(),
                                                                            pd.Timestamp.utcnow(),
                                                                            freq=pd.Timedelta(hours=1)))
        reindexed_transactions = pd.concat([cleaned_transactions, reindexed_transactions], axis=0).sort_index()
        reindexed_transactions['in_staking'].fillna(method="ffill", inplace=True)
        daily_staking_mask = reindexed_transactions.groupby(reindexed_transactions.index.date).sum()['in_staking'] > 0

        # 2. Then, we compute the totals for each day
        daily_proof_transactions = proof_transactions.groupby(proof_transactions['time'].dt.date).sum()
        reindex_daily_proof_transactions = daily_proof_transactions.reindex(daily_staking_mask.index).fillna(0)
        reindex_daily_proof_transactions[~daily_staking_mask] = np.nan
        total_amount = reindex_daily_proof_transactions['amount']
        total_amount_eur = reindex_daily_proof_transactions[f'amount_price_{currency}']

        total_amount.name = transactions['wallet'].iloc[0]
        total_amount_eur.name = transactions['wallet'].iloc[0]

        return total_amount, total_amount_eur

    def _compute_all_nodes_totals_df(self, nodes_addresses=None):
        if nodes_addresses is None:
            relay_db = get_relaydb("transactions")
            nodes_addresses = list(relay_db.keys())

        total_amounts = []
        total_amounts_eur = []

        for node_address in nodes_addresses:
            total_amount, total_amount_eur = self._compute_amount_totals(node_address)
            total_amounts.append(total_amount)
            total_amounts_eur.append(total_amount_eur)

        total_amounts_df = pd.concat(total_amounts, axis=1)
        total_amounts_eur_df = pd.concat(total_amounts_eur, axis=1)

        return total_amounts_df, total_amounts_eur_df

    @staticmethod
    def _generate_rewards_stats_df(total_amounts_df, total_amounts_eur_df):
        config = get_config()
        currency = config.get("PRICE.currency", "eur")
        currency_upper = currency.upper()

        avg_day = total_amounts_df.mean(axis=1, skipna=True)
        total_day = total_amounts_df.sum(axis=1, skipna=True)

        avg_eur_day = total_amounts_eur_df.mean(axis=1, skipna=True)
        total_eur_day = total_amounts_eur_df.sum(axis=1, skipna=True)

        total_day.index = pd.DatetimeIndex(total_day.index)
        avg_day.index = pd.DatetimeIndex(avg_day.index)

        total_eur_day.index = pd.DatetimeIndex(total_eur_day.index)
        avg_eur_day.index = pd.DatetimeIndex(avg_eur_day.index)

        now = pd.Timestamp.now()
        today = now.date()
        this_month = pd.to_datetime(np.asarray([today]).astype('datetime64[M]')[0])

        # We exclude current day from the avg earns daily
        avg_day_filtered = avg_day[avg_day.index.date < today]
        avg_earns_daily = avg_day_filtered.mean(skipna=True)
        avg_earns_today = avg_day.reindex([today]).fillna(0).iloc[0]

        # We exclude current month from the avg earns monthly
        avg_day_filtered = avg_day[avg_day.index < this_month]
        avg_earns_monthly = avg_day_filtered.groupby(
            [avg_day_filtered.index.year, avg_day_filtered.index.month]).sum().mean()

        avg_day_filtered = avg_day[(avg_day.index.year == today.year) & (avg_day.index.month == today.month)]
        avg_earns_this_month = avg_day_filtered.groupby(
            [avg_day_filtered.index.year, avg_day_filtered.index.month]).sum().mean()

        # We exclude current day from the avg earns daily
        avg_eur_day_filtered = avg_eur_day[avg_eur_day.index.date < today]
        avg_eur_earns_daily = avg_eur_day_filtered.mean(skipna=True)
        avg_eur_earns_today = avg_eur_day.reindex([today]).fillna(0).iloc[0]

        # We exclude current month from the avg earns monthly
        avg_eur_day_filtered = avg_eur_day[avg_eur_day.index < this_month]
        avg_eur_earns_monthly = avg_eur_day_filtered.groupby(
            [avg_eur_day_filtered.index.year, avg_eur_day_filtered.index.month]).sum().mean()

        avg_eur_day_filtered = avg_eur_day[
            (avg_eur_day.index.year == today.year) & (avg_eur_day.index.month == today.month)]
        avg_eur_earns_this_month = avg_eur_day_filtered.groupby(
            [avg_eur_day_filtered.index.year, avg_eur_day_filtered.index.month]).sum().mean()

        total_earns_today = total_day.reindex([today]).fillna(0).iloc[0]
        total_eur_earns_today = total_eur_day.reindex([today]).fillna(0).iloc[0]

        total_day_filtered = total_day[(total_day.index.year == today.year) & (total_day.index.month == today.month)]
        total_earns_this_month = total_day_filtered.fillna(0).sum()
        total_earns_alltime = total_day.fillna(0).sum()

        total_eur_day_filtered = total_eur_day[
            (total_eur_day.index.year == today.year) & (total_eur_day.index.month == today.month)]
        total_eur_earns_this_month = total_eur_day_filtered.reindex([today]).fillna(0).iloc[0]
        total_eur_earns_alltime = total_eur_day_filtered.fillna(0).sum()

        avg_pocket_rewards_df = pd.Series({
            "(POKT) Daily earns (avg)": avg_earns_daily,
            "(POKT) Today earns (avg)": avg_earns_today,
            "(POKT) Month earns (avg)": avg_earns_monthly,
            "(POKT) This month earns (avg)": avg_earns_this_month,
        }).round(2)

        avg_pocket_rewards_eur_df = pd.Series({
            f"({currency_upper}) Daily earns (avg)": avg_eur_earns_daily,
            f"({currency_upper}) Today earns (avg)": avg_eur_earns_today,
            f"({currency_upper}) Month earns (avg)": avg_eur_earns_monthly,
            f"({currency_upper}) This month earns (avg)": avg_eur_earns_this_month,
        }).round(2)

        total_pocket_rewards_df = pd.Series({
            f"(POKT) Today earns (total)": total_earns_today,
            f"(POKT) This month earns (total)": total_earns_this_month,
            f"(POKT) All-time earns (total)": total_earns_alltime,
        }).round(2)

        total_pocket_rewards_eur_df = pd.Series({
            f"({currency_upper}) Today earns (total)": total_eur_earns_today,
            f"({currency_upper}) This month earns (total)": total_eur_earns_this_month,
            f"({currency_upper}) All-time earns (total)": total_eur_earns_alltime,
        }).round(2)

        return avg_pocket_rewards_df, avg_pocket_rewards_eur_df, total_pocket_rewards_df, total_pocket_rewards_eur_df

    @staticmethod
    def _generate_avg_rewards_graph(total_amounts_df, last_days_count=None, currency_name="POKT"):
        # We create the figure
        fig = plt.figure(figsize=(10, 5))
        ax = fig.add_subplot(1, 1, 1)

        if last_days_count is None:
            config = get_config()
            last_days_count = int(config["CONF.last_days_stats_graph"])

        now_date = pd.Timestamp.now().date()

        avg_day = total_amounts_df.mean(axis=1, skipna=True)
        nodes_count = (~total_amounts_df.isna()).sum(axis=1)
        days_filter = avg_day.index >= now_date - pd.Timedelta(days=last_days_count)

        avg_day_filtered = avg_day[days_filter]
        nodes_count_filtered = nodes_count[days_filter]

        avg_day_filtered.index = pd.DatetimeIndex(avg_day_filtered.index)
        avg_day_filtered.name = "Average rewards"

        nodes_count_filtered.index = avg_day_filtered.index
        nodes_count_filtered.name = "Number of nodes"

        # Then we plot the graph into the figure
        avg_day_filtered.plot(title=f"Last {last_days_count} days average {currency_name.upper()} rewards by node",
                              ax=ax, secondary_y=True, legend=True, color="#00F")
        ax.bar(nodes_count_filtered.index, nodes_count_filtered.values, color="#8802", label='Number of nodes (Left)')
        ax.plot(avg_day_filtered.index, avg_day_filtered.values * np.nan, color="#00F", label='Average rewards (Right)')
        ax.yaxis.set_visible(True)
        ax.xaxis_date()
        ax.legend()
        plt.grid()

        with io.BytesIO() as buf:
            fig.savefig(buf, format='jpg')
            buf.seek(0)
            image_bytes = buf.read()

        plt.close(fig)

        return image_bytes
