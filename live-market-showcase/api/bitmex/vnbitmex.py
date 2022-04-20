
from __future__ import print_function
import hashlib
import hmac
import json
import ssl
import traceback

from queue import Queue, Empty
from multiprocessing.dummy import Pool
from time import time
# from urlparse import urlparse
from copy import copy
from urllib.parse import urlencode
from threading import Thread

from six.moves import input

import requests
import websocket


REST_HOST = 'https://www.bitmex.com/api/v1'
WEBSOCKET_HOST = 'wss://www.bitmex.com/realtime'




########################################################################
class BitmexRestApi(object):
    """REST API"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.apiKey = ''
        self.apiSecret = ''

        self.active = False
        self.reqid = 0
        self.queue = Queue()
        self.pool = None
        self.sessionDict = {}   # Session object dictionary

        self.header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

    # ----------------------------------------------------------------------
    def init(self, apiKey, apiSecret):
        """Init"""
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    # ----------------------------------------------------------------------
    def start(self, n=3):
        """start"""
        if self.active:
            return

        self.active = True
        self.pool = Pool(n)
        self.pool.map_async(self.run, range(n))

    # ----------------------------------------------------------------------
    def close(self):
        """close"""
        self.active = False

        if self.pool:
            self.pool.close()
            self.pool.join()

    # ----------------------------------------------------------------------
    def addReq(self, method, path, callback, params=None, postdict=None):
        """add Requests"""
        self.reqid += 1
        req = (method, path, callback, params, postdict, self.reqid)
        self.queue.put(req)
        return self.reqid

    # ----------------------------------------------------------------------
    def processReq(self, req, i):
        """process Requests"""
        method, path, callback, params, postdict, reqid = req
        url = REST_HOST + path
        expires = int(time() + 5)

        rq = requests.Request(url=url, data=postdict)
        p = rq.prepare()

        header = copy(self.header)
        header['api-expires'] = str(expires)
        header['api-key'] = self.apiKey
        header['api-signature'] = self.generateSignature(method, path, expires, params, body=p.body)

        # The session duration of a long connection is 80% shorter than that of a short connection
        session = self.sessionDict[i]
        resp = session.request(method, url, headers=header, params=params, data=postdict)

        # resp = requests.request(method, url, headers=header, params=params, data=postdict)

        code = resp.status_code
        d = resp.json()

        if code == 200:
            callback(d, reqid)
        else:
            self.onError(code, d)

            # ----------------------------------------------------------------------
    def run(self, i):
        """Run continuously"""
        self.sessionDict[i] = requests.Session()

        while self.active:
            try:
                req = self.queue.get(timeout=1)
                self.processReq(req, i)
            except Empty:
                pass

    # ----------------------------------------------------------------------
    def generateSignature(self, method, path, expires, params=None, body=None):
        """generate Signature"""
        # Serialize params in the HTTP message path as a request field
        if params:
            query = urlencode(sorted(params.items()))
            path = path + '?' + query

        if body is None:
            body = ''

        msg = method + '/api/v1' + path + str(expires) + body
        signature = hmac.new(self.apiSecret, msg,
                             digestmod=hashlib.sha256).hexdigest()
        return signature

    # ----------------------------------------------------------------------
    def onError(self, code, error):
        """error callbacks"""
        print('on error')
        print(code, error)

    # ----------------------------------------------------------------------
    def onData(self, data, reqid):
        """general callback"""
        print('on data')
        print(data, reqid)


########################################################################
class BitmexWebsocketApi(object):
    """Websocket API"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.ws = None
        self.thread = None
        self.active = False

    # ----------------------------------------------------------------------
    def start(self):
        """start"""
        self.ws = websocket.create_connection(WEBSOCKET_HOST,
                                              sslopt={'cert_reqs': ssl.CERT_NONE})

        self.active = True
        self.thread = Thread(target=self.run)
        self.thread.start()

        self.onConnect()

    # ----------------------------------------------------------------------
    def reconnect(self):
        """reconnect"""
        self.ws = websocket.create_connection(WEBSOCKET_HOST,
                                              sslopt={'cert_reqs': ssl.CERT_NONE})

        self.onConnect()

    # ----------------------------------------------------------------------
    def run(self):
        """run"""
        while self.active:
            try:
                stream = self.ws.recv()
                data = json.loads(stream)
                self.onData(data)
            except:
                msg = traceback.format_exc()
                self.onError(msg)
                self.reconnect()

    # ----------------------------------------------------------------------
    def close(self):
        """close"""
        self.active = False

        if self.thread:
            self.thread.join()

    # ----------------------------------------------------------------------
    def onConnect(self):
        """connection callback"""
        print('connected')

    # ----------------------------------------------------------------------
    def onData(self, data):
        """data callback"""
        print('-' * 30)
        l = list(data.keys())
        l.sort()
        for k in l:
            print(k, data[k])

    # ----------------------------------------------------------------------
    def onError(self, msg):
        """error callback"""
        print(msg)

    # ----------------------------------------------------------------------
    def sendReq(self, req):
        """send requests"""
        self.ws.send(json.dumps(req))





if __name__ == '__main__':
    # API_KEY = ''
    # API_SECRET = ''
    #
    # ## REST test
    # rest = BitmexRestApi()
    # rest.init(API_KEY, API_SECRET)
    # rest.start(3)
    #
    # data = {
    #     'symbol': 'XBTUSD'
    # }
    # rest.addReq('POST', '/position/isolate', rest.onData, postdict=data)
    # rest.addReq('GET', '/instrument', rest.onData)

    # WEBSOCKET test
    from types import MethodType


    def onData(self, data):
        if 'table' in data:
            if data['table'] == 'trade':
                for d in data['data']:
                    txt = '%s, %s' % (d['timestamp'], d['price'])
                    print(txt)
                print('=================')
            elif data['table'] == 'quote':
                print(data)
                for d in data['data']:
                    txt = 'bid1: %.2f, ask1: %.2f' % (d['bidPrice'], d['askPrice'])
                    print(txt)
                    print('-------------')

    ws = BitmexWebsocketApi()
    ws.onData = MethodType(onData, ws)
    ws.start()
    # req = {"op": "subscribe", "args": ['order', 'trade', 'position', 'margin']}
    req = {"op": "subscribe", "args": ['trade:XBTUSD']}  # market data
    req2 = {"op": "subscribe", "args": ['quote:XBTUSD']}  # level 10 order book
    ws.sendReq(req)
    ws.sendReq(req2)

    # expires = int(time())
    # method = 'GET'
    # path = '/realtime'
    # msg = method + path + str(expires)
    # signature = hmac.new(API_SECRET, msg, digestmod=hashlib.sha256).hexdigest()

    # req = {
    # 'op': 'authKey',
    # 'args': [API_KEY, expires, signature]
    # }

    # ws.sendReq(req)

    # req = {"op": "subscribe", "args": ['order', 'execution', 'position', 'margin']}
    # req = {"op": "subscribe", "args": ['instrument']}
    # ws.sendReq(req)



