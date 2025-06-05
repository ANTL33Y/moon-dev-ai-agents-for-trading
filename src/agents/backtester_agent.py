"""
🌙 Moon Dev's Backtester Agent
Runs a simple backtest on generated strategies and saves them if profitable.
"""

import os
import importlib.util
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
from statistics import mean

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

    def backtest(self, strategy: BaseStrategy, days: int = 5, timeframe: str = "1H", hold_period: int = 1):
        """Run a slightly more thorough backtest over recent data"""
        returns = []
        for token in MONITORED_TOKENS:
            df = n.get_data(token, days_back_4_data=days, timeframe=timeframe)
            if df is None or df.empty or len(df) <= hold_period:
                continue
            # iterate through dataset and evaluate signals using trailing window
            for i in range(len(df) - hold_period - 1):
                data_slice = df.iloc[: i + 1]
                try:
                    signal = strategy.generate_signals(token=token, data=data_slice)  # type: ignore[arg-type]
                except TypeError:
                    signal = strategy.generate_signals()
                if not signal:
                    continue
                direction = signal.get("direction")
                if direction not in ["BUY", "SELL"]:
                    continue
                entry = df["Close"].iloc[i]
                exit_price = df["Close"].iloc[i + hold_period]
                ret = (
                    (exit_price - entry) / entry
                    if direction == "BUY"
                    else (entry - exit_price) / entry
                )
                returns.append(ret)
        if not returns:
            return {"avg_return": 0.0, "win_rate": 0.0, "trades": 0}
        avg_ret = mean(returns)
        win_rate = sum(1 for r in returns if r > 0) / len(returns)
        return {"avg_return": avg_ret, "win_rate": win_rate, "trades": len(returns)}

    def validate_and_save(self, code: str, threshold: float = 0.0):
        """Backtest code and keep it if average return above threshold"""
        strategy_cls, path = self.load_strategy(code)
        if not strategy_cls:
            cprint("No valid strategy class found", "red")
            os.remove(path)
            return False
        strategy = strategy_cls()
        result = self.backtest(strategy)
        cprint(
            f"Backtest result: {result['avg_return']*100:.2f}% | Win rate: {result['win_rate']*100:.1f}% over {result['trades']} trades",
            "cyan",
        )
        if result["avg_return"] > threshold:
            cprint(f"Strategy saved to {path}", "green")
            return True
        os.remove(path)
        cprint("Strategy discarded due to poor performance", "yellow")
        return False

