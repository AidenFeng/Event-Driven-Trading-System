from qsDataStructure import Orderbook, Tick, Bar, Snapshot
from qsObject import DataHandler
from event.eventEngine import Event
from event.eventType import EVENT_ORDERBOOK, EVENT_TICK, EVENT_BAR_OPEN, EVENT_BAR_CLOSE
from bitmex.bitmexWSMarket import bitmexWSMarket
from bitmex.bitmexREST import bitmexREST
from bitmex.utils import calculate_td_ts
from qsUtils import generate_logger, now
import queue
import threading


class bitmexDataHandler(DataHandler):

    def __init__(self, g, account_settings):

        self.g = g                                                           # global settings
        self.logger = generate_logger('DataHandler', g.loglevel, g.logfile)  # log

        self.account_settings = account_settings  # account settings
        self.symbols = None                       # subscribed symbols  ['XBTUSD', ...]

        self.market_data_q = queue.Queue()    # MarketData queue（with data）
        self.td_run = None                    # __run() function thread
        self.active = False

        self.tick = {}            # {symbol: Tick}            # the latest last_price information
        self.orderbook = {}       # {symbol: Orderbook}       # latest orderbook information

        self.registered_tick_events = {}         # {'XBTUSD': True}      # todo BITMEX_TICK_BATCH
        self.registered_orderbook_events = {}    # {'XBTUSD': BITMEX_ORDERBOOK_TOP}   # todo: consts.py different orderbook types

        self.registered_bar_events = {}   # {'XBTUSD': ['1m', '30s'], ...}
        self.bar = {}                     # {'XBTUSD': {'1m': Bar, '30s': Bar}, ...}
        self.prev_bar = {}                # {'XBTUSD': {'1m': Bar, '30s': Bar}, ...}

    def set_symbols(self, symbols):
        self.symbols = symbols
        
    def start(self):
        self.__construct_bm_ws_market()
        self.td_run = threading.Thread(target=self.__run)
        self.active = True
        self.td_run.start()

    def get_init_data(self):
        pass

    def __run(self):  
        while self.active:
            try:
                data = self.market_data_q.get(timeout=10)
            except queue.Empty:
                self.logger.warning('no data in market_data_q for 10 seconds')
            else:
                if isinstance(data, Tick):
                    self.processTick(data)
                elif isinstance(data, Orderbook):
                    self.processOrderbook(data)
                else:
                    self.logger.warning('Invalid data type from market_data_q: %s' % data.__class__)
    
    def stop(self):
        self.logger.info('Stopping DataHandler ...')
        self.bm_ws_market.exit()
        if True:
            self.logger.info('Exiting Thread: _DataHandler.__run(), wait for less than 10 secs')
            self.active = False
            self.td_run.join()
        self.logger.info('DataHandler stopped')

    def __construct_bm_ws_market(self):
        self.bm_ws_market = bitmexWSMarket(apiKey=None, apiSecret=None, isTestNet=self.account_settings.isTestNet,
                                           loglevel=self.g.loglevel, logfile=self.g.logfile)
        self.bm_ws_market.connect()
        self.bm_ws_market.add_market_data_q(self.market_data_q)
        for s in self.symbols:
            self.bm_ws_market.subscribe(s, trade=True, orderbook=True)
        self.bm_ws_market.wait_for_data()

    def processTick(self, tick):
        self.logger.debug('💛 💛 💛 Processing Tick... %s' % tick)

        # order： bar_close_event, bar_open_event, tick_event

        # 0. generate bar
        if self.registered_bar_events.get(tick.symbol):
            if self.get_current_tick(tick.symbol) is None:   # edge case: if single tick
                # self.__update_tick(tick)
                self.__init_bar(tick.symbol, tick)
            else:
                self.__bar(tick)

        # 1. update tick(last_price)
        self.__update_tick(tick)
        
        # 2. if symbol subsribed tick event, push(global event queue)
        if self.registered_tick_events.get(tick.symbol):
            self.__push_tick_event(tick.symbol)
    
    def processOrderbook(self, ob):
        self.logger.debug('💜 💜 💜️ Processing Orderbook... %s' % ob)
        
        # 1. update Orderbook
        self.__update_orderbook(ob)
        
        # 2. if symbol subsribed orderbook event, push(global event queue)
        if self.registered_orderbook_events.get(ob.symbol):
            self.__push_orderbook_event(ob.symbol)

    def __update_tick(self, tick):
        tick.receive_time = now()
        self.tick[tick.symbol] = tick

    def __update_orderbook(self, ob):
        ob.receive_time = now()
        self.orderbook[ob.symbol] = ob

    def __push_tick_event(self, symbol):
        e = Event(type_=EVENT_TICK % symbol)
        e.dict_ = {'symbol': symbol}
        self.event_engine.put(e)
    
    def __push_orderbook_event(self, symbol):
        e = Event(type_=EVENT_ORDERBOOK % symbol)
        e.dict_ = {'symbol': symbol}
        self.event_engine.put(e)

    def register_orderbook_event(self, symbol):
        self.registered_orderbook_events[symbol] = True

    def register_tick_event(self, symbol):
        self.registered_tick_events[symbol] = True
    
    def register_bar_event(self, symbol, bar_type):
        """what type of bar is generated

        update self.registered_bar_events,  which is {symbol: ['1m', '30s'], ...}
        init self.bar, self.prev_bar
        """
        if symbol not in self.symbols:
            self.logger.warning('registering symbol "%s" of bar_type "%s", '
                                'but symbol not in self.symbols: %s' % (symbol, bar_type, self.symbols))
            return
        if symbol not in self.registered_bar_events:
            self.registered_bar_events[symbol] = []
            self.bar[symbol] = {}
            self.prev_bar[symbol] = {}
        if bar_type not in self.registered_bar_events[symbol]:
            self.registered_bar_events[symbol].append(bar_type)
            self.logger.info('Registered. %s: %s' % (symbol, bar_type))
            self.bar[symbol][bar_type] = Bar()
            self.prev_bar[symbol][bar_type] = Bar()
        else:
            self.logger.info('Registering bar: bar_type "%s" already exist in symbol "%s"' % (bar_type, symbol))

    def __init_bar(self, symbol, tick):
        """Called when a tick of the symbol is obtained.
        use tick to initalize all bar_type using the type of first bar
        """
        if symbol in self.bar:
            for bar_type in self.bar[symbol]:
                td, ts = calculate_td_ts(tick.timestamp, bar_type)
                bar = Bar(symbol=symbol, bar_type=bar_type, td=td, ts=ts, open=tick.price, high=tick.price, low=tick.price)
                self.bar[symbol][bar_type] = bar
                self.logger.debug('💙 __init_bar() 💙 %s %s 💙 self.bar: %s' % (symbol, bar_type, self.bar[symbol][bar_type]))
                prev_bar = Bar(symbol=symbol, bar_type=bar_type, td=td, ts=ts-1)
                self.prev_bar[symbol][bar_type] = prev_bar
                self.logger.info('💙 __init_bar() 💙 %s %s 💙 self.prev_bar: %s' % (symbol, bar_type, self.prev_bar[symbol][bar_type]))

    def __bar(self, tick):
        symbol = tick.symbol
        bar_types = self.registered_bar_events[symbol]

        for bar_type in bar_types:

            current_bar = self.get_current_bar(symbol, bar_type)
            current_tick = self.get_current_tick(symbol)  # 注意此时tick还未更新
            assert isinstance(current_bar, Bar), 'current_bar.__class__ is %s' % current_bar.__class__
            assert isinstance(current_tick, Tick), 'current_tick.__class__ is %s' % current_tick.__class__

            td, ts = calculate_td_ts(tick.timestamp, bar_type)

            if (td, ts) > (current_bar.td, current_bar.ts):
                # bar_close
                current_bar.close = current_tick.price
                current_bar.receive_time = now()
                self.prev_bar[symbol][bar_type] = current_bar  # move to prev_bar
                self.bar[symbol][bar_type] = None
                self.__push_bar_close_event(symbol, bar_type)
                # bar_open
                self.bar[symbol][bar_type] = Bar(symbol=symbol, bar_type=bar_type, td=td, ts=ts,
                                                 open=tick.price, high=tick.price, low=tick.price, close=None,
                                                 timestamp=tick.timestamp, receive_time=None)
                self.__push_bar_open_event(symbol, bar_type)
            else:
                self.bar[symbol][bar_type].high = max(tick.price, current_bar.high)
                self.bar[symbol][bar_type].low = min(tick.price, current_bar.low)

    def __push_bar_close_event(self, symbol, bar_type):
        e_type = EVENT_BAR_CLOSE % (symbol, bar_type)
        e = Event(type_=e_type)
        e.dict_ = {'symbol': symbol, 'bar_type': bar_type}
        self.event_engine.put(e)
        self.logger.info('💙 💙 💙  pushing bar_close_event__%s__%s__, prev_bar is %s' % (symbol, bar_type, self.prev_bar[symbol][bar_type]))

    def __push_bar_open_event(self, symbol, bar_type):
        e_type = EVENT_BAR_OPEN % (symbol, bar_type)
        e = Event(type_=e_type)
        e.dict_ = {'symbol': symbol, 'bar_type': bar_type}
        self.event_engine.put(e)
        self.logger.info('💙 💙 💙  pushing bar_open_event__%s__%s__, bar is %s' % (symbol, bar_type, self.bar[symbol][bar_type]))

    def get_current_bar(self, symbol, bar_type):
        try:
            return self.bar.get(symbol).get(bar_type)
        except AttributeError:
            return None

    def get_prev_bar(self, symbol, bar_type):
        try:
            return self.prev_bar.get(symbol).get(bar_type)
        except AttributeError:
            return None

    def get_current_tick(self, symbol):
        return self.tick.get(symbol)

    def snapshot(self, symbol):
        """Refer to domestic futures snapshot data structure"""
        pass
    
    