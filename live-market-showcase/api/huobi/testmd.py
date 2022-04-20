from .vnhuobi import HuobiDataApi

import datetime
from types import MethodType


def ts2datetime(ts):
    return datetime.datetime.utcfromtimestamp(ts / 1e3).strftime('%Y-%m-%d %H:%M:%S.%f')


def my_onTradeDetail(self, data):
    """
    {
        'ts': 1540970705871,
        'ch': 'market.ethusdt.trade.detail',
        'tick': {
                    'ts': 1540970705763,
                    'id': 26533593848,
                    'data': [
                        {'price': 196.78,
                        'amount': 0.0018,
                        'ts': 1540970705763,
                        'direction': 'buy',
                        'id': 2653359384815713142585}
                    ]
                }
    }
    """
    # print(data)
    try:
        exchagnePubTime = ts2datetime(data['ts'])
        print('-------------', data['ch'])
        for d in data['tick']['data']:
            exchagneMatchTime = ts2datetime(d['ts'])
            txt = '%s, %s, %s' % (exchagnePubTime, exchagneMatchTime, d['price'])
            print(txt)
        print('========================================')
    except Exception as e:
        print('Error ----------------')
        print(e)


def my_onMarketDepth(self, data):
    """
    {
        'ts': 1541320023064,
        'tick': {
                    'ts': 1541320023024,
                    'version': 26926812112,
                    'asks': [[6391.3, 0.0042], [6391.62, 0.02], ...],
                    'bids': [[6391.29, 0.0935], [6391.28, 0.24], ...]
                },
        'ch': 'market.btcusdt.depth.step0'
    }
    """
    try:
        exchagnePubTime = ts2datetime(data['ts'])
        print('----------------', data['ch'])
        for i in range(5):
            txt = '%s, ask%d: %.2f, bid%d: %.2f' % (exchagnePubTime, i+1 , data['tick']['asks'][i][0], i+1, data['tick']['bids'][i][0])
            print(txt)
        print('========================================')
    except Exception as e:
        print('Error ----------------')
        print(e)


api = HuobiDataApi()

api.onTradeDetail = MethodType(my_onTradeDetail, api)
api.onMarketDepth = MethodType(my_onMarketDepth, api)

api.connect("wss://api.huobipro.com/ws")

api.subscribeMarketDepth('btcusdt')
api.subscribeTradeDetail('btcusdt')
# api.subscribeMarketDetail('ethusdt')


