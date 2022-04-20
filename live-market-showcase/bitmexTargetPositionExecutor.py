from qsObject import TargetPositionExecutor
from event.eventType import EVENT_TARGET_POSITION
from event.eventEngine import Event
from qsDataStructure import Tick, Orderbook

from bitmex.bitmexWSTrading import bitmexWSTrading
from bitmex.bitmexREST import bitmexREST
from bitmex.bitmexInstruments import instruments
from bitmexDataHandler import bitmexDataHandler
from qsUtils import generate_logger


class bitmexTargetPositionExecutor(TargetPositionExecutor):

    """ Algorithmic trading logic based on target positions

    1. Counterbid order
    Exceed 1 minute did not clinch a deal, and price has moved to adverse direction, withdraw sheet to be hanged afresh.
    2. Signal price + slip point
    no deal -> FillEvent
    3. Last_price + slide point
    If there is no transaction in more than 1 minute and the price moves in an unfavorable direction, suspend the transaction again according to the latest last_price
    """

    """基于目标仓位的算法交易逻辑

    1. 对手价挂单
    超过1分钟未成交，且盘口价格已经向不利方向变动，则撤单重新挂。
    2. 信号价 + 滑点
    不成交就算了  -> FillEvent
    3. last_price + 滑点
    超过1分钟未成交，且价格朝不利方向变动，根据最新的last_price重新挂
    """

    def __init__(self, g, account_settings, symbols):

        # global setting
        self.g = g
        self.logger = generate_logger('bitmexTargetPositionExecutor', self.g.loglevel, self.g.logfile)

        # account_settings
        self.account_settings = account_settings

        # target_position
        self.target_position = {}       # {symbol: pos}

        # symbols
        self.symbols = symbols     # Subscribe to position information on which benchmarks

        # data_handler
        self.data_handler = None

        # event engine
        self.event_engine = None

        # websocket-trading
        self.bm_ws_trading = bitmexWSTrading(self.account_settings.apiKey, self.account_settings.apiSecret, self.account_settings.isTestNet)
        self.bm_ws_trading.connect()
        self.bm_ws_trading.subscribe(self.symbols)
        self.bm_ws_trading.wait_for_initial_status()  # Waiting for initial information

        self.actual_position = self.bm_ws_trading.actual_position  # The actual position 'position' calculated from the information received by the Websocket
        self.unfilled_qty = self.bm_ws_trading.unfilled_qty  # The uncompleted delegate 'order' calculated from the information received by the Websocket

        # rest
        self.bm_rest = bitmexREST(self.account_settings.apiKey, self.account_settings.apiSecret)

    def set_symbols(self, symbols):
        self.symbols = symbols

    def on_target_position_event(self, event):
        # < EventObject > type_ = eTargetPosition, dict_ = {'XBTUSD': 0}
        assert isinstance(event, Event)
        assert event.type_ == EVENT_TARGET_POSITION

        for symbol, pos in event.dict_.items():
            old_pos = self.target_position.get(symbol)
            if pos != old_pos:
                self.__update_target_position(symbol, pos)
                self.__trade_to_target(symbol)

    def on_orderbook_event(self, event):
        """Orderbook event callback function

        Are there any outstanding orders? Yes -> Has the price of the order moved in an adverse direction after a certain period of time? Yes - "Call __trade_to_target()
        """
        pass

    def on_tick_event(self, event):
        """Orderbook event callback function

        Are there any outstanding orders? Yes -> Has the last_price moved in an unfavorable direction for a certain amount of time? Yes - "Call __trade_to_target()
        """
        pass

    def __update_target_position(self, symbol, pos):
        self.target_position[symbol] = pos

    def __trade_to_target(self, symbol):
        """
        First withdraw all orders, re-order
        """
        if symbol not in self.symbols:
            self.logger.warning('Calling `trade_to_target` but arg `symbol` is not in self.symbols\n' +
                                'symbol=%s\nself.symbols=%s' % (symbol, self.symbols))
            return

        target_pos = self.target_position.get(symbol, None)  # int
        actual_pos = self.actual_position.get(symbol, 0)  # int

        if target_pos is None:
            self.logger.warning('Calling `trade_to_target()` but arg `symbol` is not in self.target_position\n' +
                                'symbol=%s\nself.target_position=%s' % (symbol, self.target_position))
            return


        if target_pos == actual_pos:
            unfilled_qty = self.unfilled_qty[symbol]  # {'Buy': 1, 'Sell': 1}
            total_unfilled_qty = sum([abs(x) for x in unfilled_qty.values()])
            if total_unfilled_qty == 0:
                self.logger.info('target_pos == actual_pos && unfilled_qty is 0, nothing to do')
            else:
                self.bm_rest.cancel_all_orders(symbol)
        else:
            self.bm_rest.cancel_all_orders(symbol)  # cancel all
            # re-construct order
            pos_diff = target_pos - actual_pos
            side = 'Buy' if pos_diff > 0 else 'Sell'
            drc = 1 if side == 'Buy' else -1
            if symbol in instruments:
                slippage = instruments[symbol].tickSize * 5
            else:
                self.logger.warning('Invalid symbol "%s": not found in bitmex.bitmexInstruments.instruments' % symbol)
                slippage = 0
            # last_price as order-limit-price
            assert isinstance(self.data_handler, bitmexDataHandler)
            current_tick = self.data_handler.get_current_tick(symbol)
            assert isinstance(current_tick, Tick)
            last_price = current_tick.price
            price = last_price + drc * slippage

            # make order
            try:
                res = self.bm_rest.place_order(symbol=symbol, side=side, qty=abs(pos_diff), limit_price=price)
            except Exception as e:
                print('❌ ❌ When placing order, an Error raise:\n %s' % e)
            else:
                if res.ok:
                    self.logger.info('Successfully Place Order:\n%s' % res.json())
                else:
                    self.logger.info('❌ ❌ ❌  Placeing Order Failed:\n%s' % res.json())

    def test(self):
        """Unit Test

        发单测试：单开一个线程，不断push TARGET_POSITION_EVENT，主动调用 on_target_position_event()
        延迟测试：收集4个时间戳，分析各种下单延迟

        :return:
        """
        pass


if __name__ == '__main__':
    import time
    from bitmex.bitmexAccountSettings import bitmexAccountSettings
    from ctaEngine import GlobalSettings

    g = GlobalSettings()
    g.from_config_file('./global_settings.json')

    bitmex_account_settings = bitmexAccountSettings()
    bitmex_account_settings.from_config_file('bitmex/BITMEX_connect.json', which="account_test")

    oms = bitmexTargetPositionExecutor(g, bitmex_account_settings, ['XBTUSD'])

    oms.test()
