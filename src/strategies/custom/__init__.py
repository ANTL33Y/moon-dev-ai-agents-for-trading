"""
🌙 Moon Dev's Custom Strategies Package
"""
from src.strategies.base_strategy import BaseStrategy
from .example_strategy import ExampleStrategy

__all__ = ['ExampleStrategy']

try:  # optional private strategy, ignored if not present
    from .private_my_strategy import MyStrategy
    __all__.append('MyStrategy')
except ImportError:  # pragma: no cover - private file may not exist
    MyStrategy = None
