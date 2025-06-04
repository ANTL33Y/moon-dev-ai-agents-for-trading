# 🌙 Moon Dev's Trading Strategies

## Overview
This directory contains the base strategy class and custom trading strategies for Moon Dev's AI Trading System.

## Structure
```
strategies/
├── base_strategy.py      # Base class all strategies inherit from
├── custom/              # Directory for your custom strategies
│   ├── __init__.py
│   ├── example_strategy.py
│   ├── open_interest_momentum.py
│   └── private_my_strategy.py
└── __init__.py
```

## How It Works
1. All strategies must inherit from `BaseStrategy`
2. Each strategy must implement `generate_signals()` method
3. Signals are evaluated by the LLM before execution
4. Approved signals are executed with position sizing based on signal strength

## Creating a Custom Strategy
1. Create a new file in `custom/` directory
2. Inherit from `BaseStrategy`
3. Implement `generate_signals()` returning:
```python
{
    'token': str,          # Token address
    'signal': float,       # Signal strength (0-1)
    'direction': str,      # 'BUY', 'SELL', or 'NEUTRAL'
    'metadata': dict       # Optional strategy-specific data
}
```

## Example Strategy
```python
from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Custom Strategy 🚀")
    
    def generate_signals(self) -> dict:
        return {
            'token': 'TOKEN_ADDRESS',
            'signal': 0.85,        # 85% confidence
            'direction': 'BUY',
        'metadata': {
            'reason': 'Strategy-specific reasoning',
            'indicators': {'rsi': 28, 'trend': 'bullish'}
        }
    }
```

## Open Interest Momentum Strategy
This strategy combines spikes in overall open interest with short-term price momentum.
It uses `MoonDevAPI.get_open_interest()` to track total open interest and `nice_funcs.get_data()`
for recent price action. If open interest increases more than 1% alongside
rising prices, it issues a **BUY** signal. If open interest drops more than 1%
while price falls, it issues a **SELL** signal.
