from poktbot.api import get_observer
from poktbot.api.node import PocketNodeTransactions
from poktbot.api.price import Coingecko
from poktbot.api.releases.pypi import PyPI
from poktbot.callbacks import CallbackStoreTransactions, CallbackStorePrices, CallbackNotifyRelease
from poktbot.config import get_config
from poktbot.telegram import TelegramBot


def main():
    config = get_config()

    # We load the database and the telegram bot
    bot = TelegramBot()

    # Generate the observers for nodes (transactions & errors), prices and new bot releases
    observer_nodes_transactions = get_observer("nodes_transactions")
    observer_prices = get_observer("prices")
    observer_releases = get_observer("releases")

    # We fill the observers with nodes with the nodes we want to observe
    for node_address in config['SERVER.nodes']:
        observer_nodes_transactions.add(PocketNodeTransactions(node_address=node_address))

    # The observer of prices with the prices we want to observe
    observer_prices.add(Coingecko())

    # And the observer of new PoktBot releases
    observer_releases.add(PyPI())

    # Finally, we observe both observers. Why? because we want both to be updated together so that we can match the
    # transaction times with their prices in the price provider. Also, on update we want to store everything in a
    # database.
    observer_main = get_observer("main")
    observer_main.add(observer_nodes_transactions)
    observer_main.add(observer_prices)
    observer_main.add(observer_releases)

    # Now we create the callbacks.
    callback_store_transactions = CallbackStoreTransactions()
    callback_store_prices = CallbackStorePrices()
    callback_notify_release = CallbackNotifyRelease(bot)

    # When the main observer gets updated, we store everything in a database
    observer_main.add_callback(callback_store_transactions)
    observer_main.add_callback(callback_store_prices)

    # And if a new release is available, a notification too.
    observer_releases.add_callback(callback_notify_release)

    # We only start the main observer because we want all the observers to be updated together.
    observer_main.start()

    bot.start()

    try:
        bot.join()
    except KeyboardInterrupt:
        bot.stop()
        observer_main.stop()


if __name__ == "__main__":
    main()
