# copy from vnpy/vnpy/event/

'''
This file is only used to store definitions of event type constants.
Since there is no real concept of constants in Python, we choose to use all-caps variable names instead of constants.
The naming convention designed here begins with the EVENT_prefix.
The content of a constant is usually a string that represents the true meaning (easy to understand).
It is recommended to place all constant definitions in this file to check for duplication.
'''

#
# EVENT_TIMER = 'eTimer'  # Timer event, sent every 1 second
#
#
# # system related
# EVENT_TIMER = 'eTimer'                  # 计时器事件，每隔1秒发送一次
# EVENT_LOG = 'eLog'                      # 日志事件，全局通用
#
# # Gateway相关
# EVENT_TICK = 'eTick.'                   # TICK行情事件，可后接具体的vtSymbol
# EVENT_TRADE = 'eTrade.'                 # 成交回报事件
# EVENT_ORDER = 'eOrder.'                 # 报单回报事件
# EVENT_POSITION = 'ePosition.'           # 持仓回报事件
# EVENT_ACCOUNT = 'eAccount.'             # 账户回报事件
# EVENT_CONTRACT = 'eContract.'           # 合约基础信息回报事件
# EVENT_ERROR = 'eError.'                 # 错误回报事件


# todo: move some events to CTA module, eg. bar_event, target_position_event

# 市场行情相关

EVENT_MARKET = 'eMarket'          # 通用市场行情事件

EVENT_ORDERBOOK = 'eOrderbook_%s'    # ORDERBOOK行情事件
EVENT_TICK = 'eTick_%s'              # TICK行情事件
EVENT_SNAPSHOT = 'eSnapshot'      # 快照行情事件，500ms切片
EVENT_BAR_OPEN = 'eBarOpen_%s_%s'       # BAR_OPEN + symbol + bar_type
EVENT_BAR_CLOSE = 'eBarClose_%s_%s'     # BAR_CLOSE + symbol + bar_type


# 策略信号相关
EVENT_SIGNAL = 'eSignal'          # 策略信号事件

# 交易相关

EVENT_TARGET_POSITION = 'eTargetPosition'   # 目标仓位事件

