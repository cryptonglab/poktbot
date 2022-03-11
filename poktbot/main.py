from poktbot.api import get_observer
from poktbot.api.node import PocketNodeTransactions, PocketNodeErrors
from poktbot.api.price import Coingecko
from poktbot.callbacks import CallbackStoreTransactions, CallbackStoreErrors, CallbackNotifyErrors, \
    CallbackStorePrices, CallbackNotifyStaking
from poktbot.config import get_config
from poktbot.telegram import TelegramBot


def main():
    config = get_config()

    # We load the database and the telegram bot
    bot = TelegramBot()

    # Generate the observers for nodes (transactions & errors) and prices
    observer_nodes_transactions = get_observer("nodes_transactions")
    observer_nodes_errors = get_observer("nodes_errors")
    observer_prices = get_observer("prices")

    # We fill the observers of nodes with the nodes we want to observe
    for node_address in config['SERVER.nodes']:
        observer_nodes_transactions.add(PocketNodeTransactions(node_address=node_address))
        observer_nodes_errors.add(PocketNodeErrors(node_address=node_address))

    # And the observer of prices with the prices we want to observe
    observer_prices.add(Coingecko())

    # Finally we observe both observers. Why? because we want both to be updated together so that we can match the
    # transaction times with their prices in the price provider. Also on update we want to store everything in a
    # database.
    observer_main = get_observer("main")
    observer_main.add(observer_nodes_transactions)
    observer_main.add(observer_nodes_errors)
    observer_main.add(observer_prices)

    # Now we create the callbacks.
    callback_notify_errors = CallbackNotifyErrors(bot)
    callback_notify_staking = CallbackNotifyStaking(bot)

    callback_store_transactions = CallbackStoreTransactions(notify_staking_callback=callback_notify_staking)
    callback_store_errors = CallbackStoreErrors(notify_callback=callback_notify_errors)
    callback_store_prices = CallbackStorePrices()

    # When the main observer gets updated, we store everything in a database
    observer_main.add_callback(callback_store_transactions)
    observer_main.add_callback(callback_store_errors)
    observer_main.add_callback(callback_store_prices)

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
