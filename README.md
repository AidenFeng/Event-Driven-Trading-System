

# Event-Driven Backtesting System

> This is just a minimum viable deliverable with my own notes, if you want to do it in a more systematic way please refer to https://www.quantstart.com/

## What is a event-driven system?
As a Data Scientist or Quant Analyst, most of the daily programming application scenarios are Data analysis or strategy backtesting, which determines that the code written by such people is more throw-away scripts executed sequentially. The corresponding Programming approach is used to Procedure Oriented Programming.

Sequential execution of scripting procedures, procedures are very simple, step by step in order to execute steps 1, 2, 3... In the real world, however, the vast majority of programs are not executed sequentially, but are determined by the user's behavior. For example, our operating system is a program that starts in a while true loop. If the user does nothing, the program keeps listening but does nothing. The handler onClick() is called when the user is listening for something, such as a mouse click. Depending on which object you click on, the onClick() function may trigger other events, which in turn trigger the corresponding handler onXXX()...

For example, video games provide a natural use case for event-driven software and provide a straightforward example to explore. A video game has multiple components that interact with each other in a real-time setting at high framerates. This is handled by running the entire set of calculations within an "infinite" loop known as the event-loop or game-loop.

```python
while True:  # Run the loop forever
    new_event = get_new_event()   # Get the latest event

    # Based on the event type, perform an action
    if new_event.type == "LEFT_MOUSE_CLICK":
        open_selected_item()
    elif new_event.type == "RIGHT_MOUSE_CLICK":
        open_action_list()
    elif new_event.type == "ESCAPE_KEY_PRESS":
        quit_game()
    # ... and many more events

    redraw_screen()   # Update the screen to provide animation
    tick(50)   # Wait 50 milliseconds
```

The code is continually checking for new events and then performing actions based on these events. In particular it allows the illusion of real-time response handling because the code is continually being looped and events checked for. As will become clear this is precisely what we need in order to carry out high frequency trading simulation.

## Why event-driven?
### 1. Code Reuse
An event-driven backtester, by design, can be used for both historical backtesting and live trading with minimal switch-out of components.
### 2. Lookahead Bias
"drip feed" an event-driven backtester with market data, replicating how an order management and portfolio system would behave.
### 3. Realism
Event-driven backtesters allow significant customisation over how orders are executed and transaction costs are incurred. It is straightforward to handle basic market and limit orders, as well as market-on-open (MOO) and market-on-close (MOC), since a custom exchange handler can be constructed.
### Drawbacks: 
1. more complex to implement and test =>  test-driven development
2. slower to execute compared to a vectorised system

## Define our components of a event-driven engine:
- An event queue
- Main thread while true loop that keeps pulling events from the event queue inside the loop body
- If the event type is A, the event processing engine calls the handlers of class A events onA1(), onA2(), onA3(), and if the event type is B, it calls the handlers of class B events onB(). These functions that handle events are sometimes called Callback funcition, which is named onSomething starting with on followed by the event name.
- When an event handler runs, new events may be generated and pushed to the end of the event queue for processing. For example onB5() may produce class C events, onC1() may produce class D events, onD9() may in turn produce class A events...
- A dictionary that holds mappings between event types and handler functions. We can set the event type and the corresponding handler before the program runs. The handler that appends a function to a particular type of event is called the register callback, and the handler that removes a function from the list of handlers for a particular type of event is called the unregister callback. We can also register or unregister callback functions dynamically during program execution: for example, onEventX() can include register_callback(A, function).

## Heres a basic example for the structure
![pic1](/event_driven.png "event-driven engine")

On the left is the event queue. There are four event types defined in the system: ABCD, shown in different colors; The program runtime is constantly trying to pull events from the event queue (while True: getEvnet()) and distribute them to different handlers (the purple EventHandlersMapping function), depending on the event type. For example, event type A calls three callback functions onA1(), onA2(), and onA3(); The callback function may also generate new events when it runs, which are pushed to the end of the queue for processing. There is also an external event source, from which the original event A was generated.

## Code Example
A simple Python code to explain this logic, you can try to run it, it works!!
```python
import queue
import time
import threading


# event queue
event_queue = queue.Queue()


# event class
class Event():  
    def __init__(self, type_):
        self.type_ = type_    # type of event
        self.dict_ = {}       # event content, normally a dictionary

# source of event
class EventSource():

    def __init__(self, q):
        self.event_queue = q   # bind to the event queue

    def run(self):
        self.run_thread = threading.Thread(target=self.__run)   # open a thread to push the events
        self.run_thread.start()

    def __run(self):
        while True:
            print('>>> Pushing event A....')
            self.event_queue.put(Event('A'))
            time.sleep(3)

# fuctions to process the events
def onA1():
    print('calling onA1()')

def onA2():
    print('calling onA2()')

def onA3():
    global event_queue
    event_queue.put(Event('B'))
    print('calling onA3()')

def onB1():
    print('calling onB1()')

def onB2():
    global event_queue
    event_queue.put(Event('C'))
    print('calling onB2()')

def onC():
    global event_queue
    event_queue.put(Event('D'))
    print('calling onC()')

def onD():
    print('calling onD()')


# trigger the source of event
event_source = EventSource(event_queue)
event_source.run()   # push an event A every 3s in another event


# Main thread: event distribution and processing logic
while True:
    try:
        event = event_queue.get(block=True, timeout=1)   # keep trying to pull events from the queue
    except queue.Empty:
        print('='*10)
    else:
        # Depending on the event type, the corresponding handler is executed. In practice the relationship between events and handlers is maintained by a {eventType:[handlers]} dictionary
        if event.type_ == 'A':
            onA1()
            onA2()
            onA3()
        elif event.type_ == 'B':
            onB1()
            onB2()
        elif event.type_ == 'C':
            onC()
        elif event.type_ == 'D':
            onD()
```

We can say that an event-driven program can be defined as a set of rules "execute onX1(), onX2() when event X occurs." We write an event-driven program and all we need to do is 1. 2. Implement various onXXX() handlers.

## Structure for a normal event-driven trading system 
### Event
   It contains a type (such as "MARKET", "SIGNAL", "ORDER" or "FILL") that determines how it will be handled within the event-loop.
### Event Queue
   The Event Queue is an in-memory Python Queue object that stores all of the Event sub-class objects that are generated by the rest of the software.
### DataHandler
   An abstract base class (ABC) that presents an interface for handling both historical or live market data. This provides significant flexibility as the Strategy and Portfolio modules can thus be reused between both approaches. The DataHandler generates a new MarketEvent upon every heartbeat of the system
### Strategy
   The Strategy is also an ABC that presents an interface for taking market data and generating corresponding SignalEvents, which are ultimately utilised by the Portfolio object. A SignalEvent contains a ticker symbol, a direction (LONG or SHORT) and a timestamp.
### Portfolio
   This is an ABC which handles the order management associated with current and subsequent positions for a strategy. It also carries out risk management across the portfolio, including sector exposure and position sizing. In a more sophisticated implementation this could be delegated to a RiskManagement class. The Portfolio takes SignalEvents from the Queue and generates OrderEvents that get added to the Queue.
### ExecutionHandler
   The ExecutionHandler simulates a connection to a brokerage. The job of the handler is to take OrderEvents from the Queue and execute them, either via a simulated approach or an actual connection to a liver brokerage. Once orders are executed the handler creates FillEvents, which describe what was actually transacted, including fees, commission and slippage (if modelled).
### The Loop
   All of these components are wrapped in an event-loop that correctly handles all Event types, routing them to the appropriate component.

```python
# Declare the components with respective parameters
bars = DataHandler(..)
strategy = Strategy(..)
port = Portfolio(..)
broker = ExecutionHandler(..)

while True:
    # Update the bars (specific backtest code, as opposed to live trading)
    if bars.continue_backtest == True:
        bars.update_bars()
    else:
        break
    
    # Handle the events
    while True:
        try:
            event = events.get(False)
        except Queue.Empty:
            break
        else:
            if event is not None:
                if event.type == 'MARKET':
                    strategy.calculate_signals(event)
                    port.update_timeindex(event)

                elif event.type == 'SIGNAL':
                    port.update_signal(event)

                elif event.type == 'ORDER':
                    broker.execute_order(event)

                elif event.type == 'FILL':
                    port.update_fill(event)

    # 10-Minute heartbeat
    time.sleep(10*60)
```

***The outer loop is used to give the backtester a heartbeat.*** For live trading this is the frequency at which new market data is polled. For backtesting strategies this is not strictly necessary since the backtester uses the market data provided in drip-feed form => bars.update_bars().

***The inner loop actually handles the Events from the events Queue object.*** Specific events are delegated to the respective component and subsequently new events are added to the queue. When the events Queue is empty, the heartbeat loop continues:

## Publish/Subscribe mode
In practice, callback functions are usually not individual functions, but rather member functions of various classes and their instances. The object that generates the event is called publisher, and the object that listens and processes the event is called subscriber. Events in the publish-subscribe pattern are also called messages.

Typically, messages are not pushed directly by publishers to subscribers, but are routed through a messaging middleware. Message middleware is responsible for message subscription or unsubscription, message filtering, message distribution, publishers and subscribers do not influence each other, even do not need to know each other's existence, to achieve loose coupling.

Our example above may not be a typical publish-subscribe pattern because some objects are both publishers and subscribers. The publish-subscribe pattern is a simple form of an event-driven model.

## Clarify requirements: a minimalist trading system
Let's leave aside for the moment the grand subject of "trading system architecture" and don't even think about writing code. First, consider the requirements: what problems does a trading system need to solve?

Here are a few requirements encountered in the actual work:

- Receive quotations. After receiving the market to have market filter (currency circle exchange is really pit, often sent over some strange prices => if there is no abnormal market filter mechanism, the strategy is absolutely dead fast)
- Most CTA strategies are based on bar, which is to combine the real-time tick into bar
- CTA multi-strategy generally adopts a variety of targets, a variety of time cycle to play the role of diversification of investment. The correspondence between (strategy, parameter) and (target, bar cycle) should be established
- Risk parity is used to adjust the weight of the portfolio according to the reciprocal of the underlying recent volatility
- Supports multiple algorithmic trading and order splitting algorithms, and different strategies specify different algorithmic trading methods
- In some transactions, multiple accounts are used to circumvent the limit on the number of times for reporting withdrawal orders, which involves the allocation of positions and margin between accounts as well as the optimization of transaction fees.
- The market chart is displayed in real time, and the information of your strategy, such as opening points, loss-stoping lines, etc., is marked on the chart. This can be manually keep an eye set on the market status, avoid the transactions triggered disorderly by any program bug.
-  Monitor the floating profit and loss of the account in real time, and automatically stop trading when the daily loss exceeds a certain limit.
- Record market information, stored in the local database for market playback when back testing.
- Backtest and real disk use a set of strategy code that is mechanically designed to avoid the common problems of backtest for future functions.
- Other external event sources. For example, climb Twitter text to do public opinion analysis; Trading bitcoins may be based on price information such as the $USD and gold.
- Other weird needs...  :(

Some of these requirements are required and some are optional. There is a concept in software development called Minimum Viable Product (MVP). It means cutting out unnecessary details at the beginning of development, leaving only the core features, in an effort to produce a working Product as quickly as possible, and then improving the Product through iteration. So what would be the simplest possible trading system? Nothing more than:

    Close market -> strategy signal -> portfolio optimization -> put order, collect transaction feedback

BTW I found an interesting point: these four requirements exactly correspond to the division of labor of public or private funds in real life:

    devs prepares data -> researcher generates strategic signal -> fund manager selects signal mix -> traders make the orders


## We now define a trading system in accordance with the event-driven programming paradigm described earlier:

- When an market quotation is received, a strategic calculation is made. Strategic calculation generates profolio signals
- When the strategy signal is received, the target position of portfolio is generated, and then the order event is issued
- When an order event is received, the specific order algorithm is executed and a "successful order" event is generated (i.e. position change event).
- Monitor portfolio position and order message, inform strategy and portfolio when receiving position change event, update current actual position information

When we stripped away all the unnecessary features, we found that the simplest trading system could do nothing more than address these four requirements. We define the event processing mapping in the transaction system while expressing the four requirements. At this point, the prototype of a trading system is fairly clear, but before we start writing it, we need to carefully analyze which classes and methods should be designed to act as callbacks for the above requirements. Consider these two questions:

How to design classes, their methods and properties, and the interaction mechanism between classes so that

1. These functions are logically grouped into appropriate classes

2. Reduce the coupling degree between classes as much as possible?

## Classes, methods, event types and their interactions in a trading system
Here is my design plan, of course, this plan is not necessarily the best, nor the only answer (in fact, according to the type of strategy, trading system architecture is very different, for example, futures CTA strategy and stock alpha strategy design must be different).

### A simple trading system needs to have at least one of the following objects/classes:

#### DataHandler. 
The data engine is responsible for receiving, validating, converting the quotation data to the appropriate format, and pushing it to the event queue.
#### The Strategy. 
Receive market info and generate corresponding signal.
#### Portfolio. 
Receive strategy signal and generate portfolio's target position
#### Executor. 
Responsible for placing orders and trade to target positions.

## The call and generation relationships between objects and events are as follows:
- When the DataHandler receives a bid (which we define as the MarketEvent), the strategy instance will execute the strategic calculation function onMarketData() accordingly. Strategy calculation functions may generate strategy signals, which we define as strategy event SignalEvent.

- The portfolio object receives the strategy signal, updates the portfolio target position, and places the orders accordingly. This logic is written in the SignalEvent callback function onSignal(). An OrderEvent OrderEvent is generated after the order request is successfully sent.

- Portfolio itself subscribes to OrderEvent, and its callback, onOrderEvent(), mainly updates the portfolio position information it maintains, adding just orders to the list of outstanding orders

- Protfolio also subscribes to FillEvent (most exchanges have this feature: By subscriing to the exchange for trades or positions, trades or any changes in positions from a trading account are constantly pushed to us. Just like the market, we assemble this information into a standard FillEvent that pushes event queues.) Similarly, the self-maintained portfolio position information is updated according to FillEvent. In addition, if the order is not completed within the specified time, a new OrderEvent is generated by order tracing, and FillEvent is generated until the actual position matches the target position.

- The transaction executor subscribes to OrderEvent and FillEvent and is responsible for the specific order logic. Typically we write algorithmic trading logic in executor objects. In some cases executors also subscribe to MarketEvent. A common way to order is to place an order for one price, which requires orderBook information in the market information.

    We can apply the above events and handlers to the previous diagram, the only difference being that the handlers here no longer try separate functions onA1(), onB1() etc. It's a member function bound to a particular class.

![pic2](/event_based_system.png "event-based system")

## Let's show a concrete example：
This might be a little vague, but let's look at a specific case. One of the simplest requirements is as follows:

    Backtesting Strategy:
    Data: Stock Index Futures IF daily data, stored in a CSV file 
    Strategy: random strategy
    Combination: only one strategy with one parameter, trade directly according to the strategy signal without processing
    Simulated trading: trading by closing price

This is a backtesting, but all we need to do is replace the CSVDataHandler that reads the CSV file with the LiveTradeDataHandler, and replacing BacktestExecutor with bitmexExecutor(for example) for real order transactions, then we can meet the need for a single set of code for back test and real order without changing Strategy and Portfolio. Using same set of code for back test and real bid can fundamentally eliminate the stealing price and other problems, now more reliable private equity institutions should have this kind of infrastructure.

```python
#################### objects && event definition ################
class CSVDataHandler(DataHandler):
    def run(self):
        # Use a single thread for market playback
        pass

    def get_prev_bars(self):
        # function: obtain the previous history of k line data
        pass

    def get_current_bars(self):
        # function: obtain the current K line data
        pass


class RandomStrategy(Strategy):
    def on_market_event(self, event):
        # put the strategy here
        pass

class NaivePortfolio(Portfolio):

    def on_signal_event(self, event):
        # aggregate signal
        pass

    def on_fill_event(self, event):
        # Update the position
        pass

    def on_market_event(self, event):
        # If you want to adjust the portfolio weight according to risk-parity...
        pass

class BarBacktestExecutor(Executor):
    def on_order_event(self, event):
        # Algorithmic trading: signal price + sliding point or to one price or the best offer queue
        # If the volume is large, to split the order: TWAP, VWAP


################## main.py ##################

event_queue = queue.Queue()   # event queue

data_handler = CSVDataHandler(event_queue, 'data/IF.csv')  # data handler

strategy = RandomStrategy(event_queue, data_handler)       # strategy instance. In practice, there should be multiple strategy instances
portfolio = NaivePortfolio(event_queue, data_handler)      # portfolio
executor = BarBacktestExecutor(event_queue, data_handler)   # Backtest simulator; in case of live trading here is the algorithmic trading module

# Launch Quote Replay
data_handler.run()

while True:
    try:
        event = event_queue.get(block=True, timeout=3)
    except queue.Empty:
        break
    else:
        # Depending on the type of event, the respective handlers are called to handle the event
        if event.type == 'MARKET':
            strategy.on_market_event(event)    # MarketEvent,Feeding to strategy, generating signals
            portfolio.on_market_event(event)    # MarketEvent, Feed to portfolio, adjust position_sizing && adjust order price limit
            executor.on_market_event(event)   # If you need to order_book to accurately estimate whether the transaction can be placed successfully...

        elif event.type == 'SIGNAL':
            portfolio.on_signal_event(event)    # signal -> portfolio

        elif event.type == 'ORDER':
            executor.on_order_event(event)    # Execution of orders

        elif event.type == 'FILL':
                portfolio.on_fill_event(event)    # Update position information based on transaction feedbacks
```


# Notes for trading cryptocurrency:
Recently, I contacted many digital currency teams when I was looking for a job. After chatting with them, I found that most of them are concentrated in 4~5 exchanges with good liquidity. The futures are basically OKEX, Bitfinix and bitMEX, while the spot bitcoins is basically trading on Huobi and Binance.

Compared with traditional futures, there are many differences in the trading rules and contract Settings of digital currency. In fact, I don't know much about them due to my CS background, but I believe I will have a deeper understanding after completing the the first semester of MFE program. I'll leave a few key directions here, and I'll catch up later when I have time:

- Reverse/non-linear contracts
- Delivery contract and perpetuity contract
- Maker-Taker
- Position and leverage, unwind positions

# Cryptocurrency Trading Interface
The interface design for digital currency exchanges is basically the same, with BitMEX as an example. Bitmex is by far the only major digital currency exchange to offer a testing environment, and is generally recognized as having the best user experience and most well-documented development. We register a test environment account, which will automatically have 0.1 XBT, and we can continue to get free coins for test purposes.
> BitMex API Overview https://testnet.bitmex.com/app/apiOverview
> 
> BitMEX Websocket Adapters https://github.com/BitMEX/api-connectors/tree/master/official-ws

# REST and websocket
The API of digital currency exchange basically adopts REST + Websocket. The technical differences between REST and Websocket won't be covered here, we just need to know:
- REST sends a request, the server will give you a response, suitable for active request functions, generally active query or order;
- Websocket is when you subscribe to a topic, the server continuously push information to you, suitable for passive receiving information function, the two most commonly used functions are to receive market and receive transaction returns.

For Quant, the REST API is straightforward to use, which is essentially an http request. The use of Websocket may need to embrace a new way of thinking. Let's start with REST and issue an order ticket with a simple HTTP request.

# REST API
We can use the interactive REST API browser provided by BitMEX to easily view each request parameter format and sample return values. The REST API endpoint is shown here, where I have highlighted several common endpoints:
> https://testnet.bitmex.com/api/explorer/
![pic3](/rest_api.png "REST API")

Green is the tick-related endpoint, which can be queried without authentication. For example, if we want to query the daily data of XBTUSD k-line in the last 5 days, we can directly run the command line by referring to the imported format of the trade endpoint parameter:
```console
curl -X GET --header 'Accept: application/json' 'https://testnet.bitmex.com/api/v1/trade/bucketed?binSize=1d&partial=false&symbol=XBTUSD&count=100&reverse=false&startTime=2018-12-01&endTime=2018-12-10'
```
The returned JSON data is then returned.

Now let's focus on the issue of order. Programmatic ordering itself is nothing new but a POST request, a undo order is a DEL request, a change order is a PUT request, and a query order is a GET request:
![pic4](/rest_order.png "REST Order")

The tricky part is authentication. All operations related to accounts and transactions (place orders, check trades, check wallet balances) definitely require proof that you are you, and in the CS world, proof that you are you is a signature verification algorithm. 

The public and private key encryption algorithm is very basic. The HMAC signature algorithm can be understood as a function. It takes two parameters: apiSecret, the content of your request (message); The signature() function returns a fixed-length string(hash). With the signature, we then send the request content and signature to the server via an HTTP request. The server side also stores your apiSecret, and will use the same algorithm to generate the signature according to your message, and compare it with the signature you sent. If they are the same, the verification will pass, otherwise the verification will not pass.
> The point of signing is that you don't need to pass apiSecret in clear text to verify that you actually sent a message; ApiSecret cannot be counterderived through signature and message, which ensures security.

Let's take a look at how to implement the order in Python. First register your account and generate a pair of apiKey, apiSecret for your account. Next refer to the official Python implementation documentation for API signing to generate a signature for an order request. Here are a few things to look out for:

#### 1. The format of message is defined as verb + path + nonce + data
- Verb specifies an HTTP request. Method: GET, POST, etc. The verb of the order is POST
- Path = Base_URL + endpoint, where Base_URL is https://testnet.bitmex.com/api/v1, endpoint is /order
- Nonce means expiry, request expiration, in the format of a Unix timestamp
- Data encodes the URL of the POST dictionary. Here we buy 20 XBTUSD contracts at market price, url-encoding is ?symbol=XBTUSD&side=Buy&orderQty=20&ordType=Market

#### 2. The signature generation function calls the Python hmax library directly:
```python
import hmac
signature = hmac.new(apiSecret, msg, digestmod=hashlib.sha256).hexdigest()
```

### 3. Request expiration times are generated dynamically in the program, for example:
```python
expires = int(round(time.time()) + 50)
```
Take the network situation into consideration and add more waiting time.

### 4. After the signature is generated, the signature and apiKey are added to the HTTP request header and sent to the exchange along with the original request.
Here is the code for generating signatures, copied from the official example, with some bug fixes. Note that this is run using python2.7:
```python
# -*- coding: utf-8 -*-

import time
import hashlib
import hmac
from urlparse import urlparse
# signature is HMAC_SHA256(secret, VERB + path + Expires + data) in hexadecimal code.
# verb must be uppercase, the URL must be relative, and the nonce must be an incrementing 64-bit integer
# data (if any) must be in JSON format with no Spaces between key values.
def generate_signature(secret, verb, url, expires, data):
    """Generate a request signature compatible with BitMEX."""
    # The URL is parsed to remove the base address to get the path
    parsedURL = urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query

    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf8')

    print("Computing HMAC: %s" % verb + path + str(expires) + data)
    message = verb + path + str(expires) + data

    signature = hmac.new(bytes(secret), bytes(message), digestmod=hashlib.sha256).hexdigest()
    return signature

expires = 1518064236
# Or you can generate it like this:
expires = int(round(time.time()) + 5)

apiKey = ''     # <<-- Fill in your apiKey here
apiSecret = ''  # <<-- Fill in your apiSecret here

signature = generate_signature(apiSecret, 'GET', '/api/v1/order', expires, 'symbol=XBTUSD&side=Buy&orderQty=20&ordType=Market')

print(signature)
```

