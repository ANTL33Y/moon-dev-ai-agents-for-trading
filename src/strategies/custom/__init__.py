"""
🌙 Moon Dev's Custom Strategies Package
"""
from src.strategies.base_strategy import BaseStrategy
from .example_strategy import ExampleStrategy
from .open_interest_momentum import OpenInterestMomentumStrategy

__all__ = ['ExampleStrategy', 'OpenInterestMomentumStrategy']

try:  # optional private strategy, ignored if not present
    from .private_my_strategy import MyStrategy
    __all__.append('MyStrategy')
except ImportError:  # pragma: no cover - private file may not exist
    MyStrategy = None
