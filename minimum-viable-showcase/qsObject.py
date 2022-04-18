from abc import ABCMeta, abstractmethod


class DataHandler(object):
    """
    DataHandler is abc proving an interface for all inherited data handlers, both live and historic
    The goal of a (derived) DataHandler object is to
        - interface to get history bars/ticks
        - "drip feed" updated bars
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_prev_bars(self, n=1, columns=None):
        raise NotImplementedError('Must implement get_latest_bars()')

    @abstractmethod
    def get_current_bar(self, columns=None):
        raise NotImplementedError('Must implement get_latest_bars()')

    @abstractmethod
    def update(self):
        raise NotImplementedError('Must implement update_bars()')


class Strategy(object):
    """
    Strategy
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_market_event(self, event):
        raise NotImplementedError('Must implement on_market_event')


class Portfolio(object):
    """
    Portfolio

    - portfolio construction
    - order management
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_signal_event(self, event):
        raise NotImplementedError('Must implement on_signal_event()')

    @abstractmethod
    def on_fill_event(self, event):
        raise NotImplementedError('Must implement on_fill_event')


class Executor(object):
    """
    Executor
    - Historical data backtesting, self-implemented simulation trading mechanism
    - Real trading matchmaking
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def on_order_event(self, event):
        raise NotImplementedError('Must implement on_order_event()')
