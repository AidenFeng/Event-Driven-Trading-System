from qsObject import Strategy
from qsEvent import MarketEvent, SignalEvent
import time
import random


class RandomStrategy(Strategy):
    """
    TurtleStrategy;
    Buy at the close when today's close is higher than the highest in the last 20 trading days;
    After buying, sell at the closing price when the closing price is lower than the lowest price in the past 10 trading days.
    """

    def __init__(self, event_queue, data_handler):
        self.event_queue = event_queue
        self.data_handler = data_handler

    def on_market_event(self, event):
        """
        MarketEvent operation function

        :param event: MarketEvent
        :return:
        """
        if event.type == 'MARKET':
            print('=== strategy === processing MarketEvent:', event)

            current_bar = self.data_handler.get_current_bar()
            print('=== strategy === current_bar: ', dict(current_bar))

            # construct SignalEvent
            symbol = 'IF'
            rand_signal = random.sample([1, 0, 1], k=1)[0]
            now = time.time()
            signal_event = SignalEvent(symbol=symbol, timestamp=now, signal_direction=rand_signal)

            # put into event queue
            self.event_queue.put(signal_event)
