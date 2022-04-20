import queue
import threading


class Event:
    """event object"""

    def __init__(self, type_=None):
        self.type_ = type_
        self.dict_ = {}

    def __repr__(self):
        return '<EventObject> type_=%s, dict_=%s' % (self.type_, self.dict_)


class eventEngine(object):
    """eventEngine (general)"""

    def __init__(self):
        self.__queue = queue.Queue()    # event queue
        self.__handlers = {}            # event handler for function mapping
        self.__general_handlers = []    # general event handler
        self.__run_thread = None        # event processing thread
        self.__active = False           # engine switch

        self.register_general_handler(self.__print_event)

    def __print_event(self, event):
        assert isinstance(event, Event)
        print('✅ ✅ ✅  Event ✅ ✅ ✅   type_=%s, dict_=%s' % (event.type_, event.dict_))

    def start(self):
        """start the engine"""
        self.__active = True
        self.__run_thread = threading.Thread(target=self.__run)
        self.__run_thread.start()

    def stop(self):
        """stop the engine"""
        self.__active = False
        self.__run_thread.join()

    def __run(self):
        """events are continually fetched from the queue and processed"""
        while self.__active:
            try:
                event = self.__queue.get(timeout=5)
            except queue.Empty:
                print('❎  eventEngine ❎  5 seconds no event')
            else:
                self.__process(event)

    def __process(self, event):
        """Depending on the event type, they are distributed to different handlers"""
        assert isinstance(event, Event)
        event_type = event.type_
        if event_type in self.__handlers:
            for func in self.__handlers[event_type]:
                func(event)
        if self.__general_handlers:
            for func in self.__general_handlers:
                func(event)

    def register(self, event_type, func):
        """Register event handlers"""
        assert callable(func), 'arg func must be callable. func is %s' % func
        if event_type not in self.__handlers:
            self.__handlers[event_type] = list()
        self.__handlers[event_type].append(func)

    def unregister(self, event_type, func):
        """Unregister the event handler"""
        if event_type in self.__handlers:
            if func in self.__handlers[event_type]:
                self.__handlers[event_type].remove(func)
            else:
                print('func %s is not in self.__handlers[event_type] list' % func)
        else:
            print('event_type %s is not in self.__handlers' % event_type)

    def register_general_handler(self, func):
        self.__general_handlers.append(func)

    def unregister_general_handler(self, func):
        if func in self.__general_handlers:
            self.__general_handlers.remove(func)

    def put(self, event):
        """Puts events into queues"""
        assert isinstance(event, Event)
        self.__queue.put(event)


def test():
    import random
    import time
    from .eventType import EVENT_MARKET, EVENT_TARGET_POSITION

    def printA(event):
        print('************** %s' % event)

    def printB(event):
        print('============== %s' % event)

    ee = eventEngine()
    ee.register(EVENT_MARKET, printA)
    ee.register(EVENT_TARGET_POSITION, printB)
    ee.start()

    while True:
        try:
            t = random.sample([EVENT_TARGET_POSITION, EVENT_MARKET], k=1)[0]
            event = Event(type_=t)
            ee.put(event)
            time.sleep(1)
        except KeyboardInterrupt:
            ee.stop()
            break


if __name__ == '__main__':
    test()