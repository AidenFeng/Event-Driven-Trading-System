from qsObject import Executor
from qsEvent import FillEvent, OrderEvent
import datetime


class BarBacktestExector(Executor):
    """
    k-line(minute) data backtesting simulative clincher

    Simulated transaction mechanism:
    - Current closing price of bar
    - Todo: The number of transactions does not exceed half of the current bar
    """

    def __init__(self, event_queue, data_handler):
        self.event_queue = event_queue
        self.data_handler = data_handler
        self.current_bar_close = None

    def on_order_event(self, event):
        print('~~~ executor ~~~ processing order event:', event)
        assert isinstance(event, OrderEvent)

        if event.type == 'ORDER':

            if event.order_type == 'MKT':
                fill = FillEvent(
                    timestamp=datetime.datetime.now(),
                    symbol=event.symbol,
                    direction=event.direction,
                    quantity=event.quantity,
                    price=self.current_bar_close,   # Deal based on current closing price
                    commission=0.0,
                    fill_flag='ALL_FILLED',
                )
                self.event_queue.put(fill)

            elif event.order_type == 'LMT':
                # todo
                pass

    def on_market_event(self, event):
        self.current_bar_close = self.data_handler.get_current_bar()['close']
        print('~~~ executor ~~~ got market event, new current_bar_clsoe: ', self.current_bar_close)
