from ctaObject import CtaStrategy
from qsDataStructure import Tick, Bar
from event.eventEngine import Event
from event.eventType import EVENT_SIGNAL
from ctaObject import CtaStrategyConfig
from qsUtils import generate_logger
import time
import random


class RandomStrategy(CtaStrategy):
    """RandomStrategy only for testing"""

    def __init__(self, config):
        super().__init__(config)

        self.target_position = 0

        self.event_engine = None
        self.data_handler = None

    def on_init(self):
        print('Calling on_init() ...........')

    def on_bar_close(self, event):
        print('Calling on_bar_close() ...........')

    def on_bar_open(self, event):
        print('Calling on_bar_open() .........')
        self.__gen_target_positon()
        self.__push_signal_event()

    def on_tick(self, event):
        print('Calling on_tick() .........')

    def __gen_target_positon(self):
        self.target_position = random.sample([-1, 0, 1], k=1)[0]

    def __push_signal_event(self):
        e = Event(type_=EVENT_SIGNAL)
        e.dict_ = {'identifier': self.identifier, 'symbol': self.symbol, 'target_position': self.target_position}
        self.event_engine.put(e)
        print('🎲 🎲 🎲 🎲  pushing signal event 🎲 🎲 🎲 🎲  strategy target_position is %s' % self.target_position)