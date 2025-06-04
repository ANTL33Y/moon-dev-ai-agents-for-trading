"""
🌙 Moon Dev's Backtester Agent
Runs a simple backtest on generated strategies and saves them if profitable.
"""

import os
import importlib.util
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv

from src.config import MONITORED_TOKENS
from src.strategies.base_strategy import BaseStrategy
from src import nice_funcs as n

class BacktesterAgent:
    """Validate strategies using historical data"""

    def __init__(self):
        load_dotenv()

    def load_strategy(self, code: str):
        """Load strategy class from code string"""
        file_name = f"generated_strategy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.py"
        path = os.path.join("src", "strategies", "custom", file_name)
        with open(path, "w") as f:
            f.write(code)
        spec = importlib.util.spec_from_file_location("generated_strategy", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        strategy_cls = None
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                strategy_cls = obj
                break
        return strategy_cls, path

    def backtest(self, strategy: BaseStrategy, days: int = 3):
        """Very naive backtest using last two candles"""
        total_return = 0
        tests = 0
        for token in MONITORED_TOKENS:
            df = n.get_data(token, days_back_4_data=days, timeframe="1H")
            if df is None or df.empty or len(df) < 2:
                continue
            signal = strategy.generate_signals()
            if not signal:
                continue
            direction = signal.get("direction")
            if direction not in ["BUY", "SELL"]:
                continue
            entry = df["Close"].iloc[-2]
            exit_price = df["Close"].iloc[-1]
            if direction == "BUY":
                ret = (exit_price - entry) / entry
            else:
                ret = (entry - exit_price) / entry
            total_return += ret
            tests += 1
        return (total_return / tests) if tests else 0

    def validate_and_save(self, code: str, threshold: float = 0.0):
        """Backtest code and keep it if average return above threshold"""
        strategy_cls, path = self.load_strategy(code)
        if not strategy_cls:
            cprint("No valid strategy class found", "red")
            os.remove(path)
            return False
        strategy = strategy_cls()
        result = self.backtest(strategy)
        cprint(f"Backtest result: {result*100:.2f}%", "cyan")
        if result > threshold:
            cprint(f"Strategy saved to {path}", "green")
            return True
        os.remove(path)
        cprint("Strategy discarded due to poor performance", "yellow")
        return False

