"""
Load all strategy classes
"""


# Every time you add a strategy, you import it here

from .RandomStrategy import RandomStrategy
from .EmaStrategy import EmaStrategy
from .TurtleStrategy import TurtleStrategy


# STRATEGY_CLASS records the mapping between ctaStrategyconfig. config_name and the policy class
# Similarly, for each policy added, a record is manually added to the dictionary

STRATEGY_CLASS = {
    'RandomStrategy': RandomStrategy,
    'EmaStrategy': EmaStrategy,
    'TurtleStrategy': TurtleStrategy
}