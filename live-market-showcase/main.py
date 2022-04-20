# DEPRECATED. use qsMainEngine.py

# main program
from bitmex.GlobalSettings import GlobalSettings
from bitmex.bitmexDataHandler import bitmexDataHandler
import queue
import time


# Loading global Settings
g = GlobalSettings()
g.from_config_file('bitmex/global_settings.json')
print('--------------------- global settings --------------------------- \n%s' % g.__dict__)


# event queue
event_q = queue.Queue()

# DataHandler
datahandler = bitmexDataHandler(g)
datahandler.add_event_q(event_q)
datahandler.register_bar_event('XBTUSD', '15s')
datahandler.run()

# datahandler.register_bar_event('XBTUSD', '1m')
# for s,bar_type in params.subscription:
#     datahandler.register_bar_event(s, bar_type)


print('=====================The main program polls the event queue==========================')
while True:
    try:
        a = event_q.get(timeout=10)
    except queue.Empty:
        print('❎  main process ❎ Warning: no data in 10 sec')
    else:
        print('✅ ✅ ✅  Main process event ✅ ✅ ✅ %s' % a)



# time.sleep(60)
# datahandler.exit()




