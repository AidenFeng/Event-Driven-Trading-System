# Main program
# Command line run
# $ python main.py


import queue
import time

from CSVDataHandler import CSVDataHandler
from RandomStrategy import RandomStrategy
from NaivePortfolio import NaivePortfolio
from BarBacktestExecutor import BarBacktestExector


event_queue = queue.Queue()   # event queue

data_handler = CSVDataHandler(event_queue, 'data/IF.csv')  # data_handler

strategy = RandomStrategy(event_queue, data_handler)       # strategy. there might be multiple strategies in practice
portfolio = NaivePortfolio(event_queue, data_handler)      # portfolio
executor = BarBacktestExector(event_queue, data_handler)   # back testing executor/ or real executor

# market playback
data_handler.run()

while True:
    try:
        event = event_queue.get(block=True, timeout=3)
    except queue.Empty:
        break
    else:
        # Depending on the type of event, the respective handlers are called to handle the event
        if event.type == 'MARKET':
            strategy.on_market_event(event)    # MarketEvent, Feeding strategy, generating signals
            portfolio.on_market_event(event)    # MarketEvent, Feed to portfolio, adjust position_sizing && adjust limit order price
            executor.on_market_event(event)   # If you need to order_book to accurately estimate whether the transaction can be made...

        elif event.type == 'SIGNAL':
            portfolio.on_signal_event(event)    # Signal -> Portfolio

        elif event.type == 'ORDER':
            executor.on_order_event(event)    # Execution of orders

        elif event.type == 'FILL':
            portfolio.on_fill_event(event)    # Update position information based on transaction feedback


