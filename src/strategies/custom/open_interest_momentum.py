from src.strategies.base_strategy import BaseStrategy
from src.agents.api import MoonDevAPI
from src.config import MONITORED_TOKENS
from src import nice_funcs as n
import pandas as pd
from termcolor import cprint

class OpenInterestMomentumStrategy(BaseStrategy):
    """Combine open interest spikes with short-term price momentum"""

    def __init__(self):
        super().__init__("Open Interest Momentum 🚀")
        self.api = MoonDevAPI()
        self.oi_threshold = 1.0  # percentage change to trigger signal

    def generate_signals(self) -> dict:
        try:
            oi_df = self.api.get_open_interest()
            if oi_df is None or len(oi_df) < 2:
                cprint("OI data not available", "red")
                return None

            oi_df['timestamp'] = pd.to_datetime(oi_df['timestamp'])
            recent = oi_df.iloc[-1]
            previous = oi_df.iloc[-2]
            oi_change = ((recent['total_oi'] - previous['total_oi']) / previous['total_oi']) * 100

            token = MONITORED_TOKENS[0]
            data = n.get_data(token, days_back_4_data=1, timeframe='15m')
            if data is None or data.empty:
                return None

            price_change = data['Close'].iloc[-1] - data['Close'].iloc[-5]
            direction = 'NEUTRAL'
            signal_strength = 0.0

            if oi_change > self.oi_threshold and price_change > 0:
                direction = 'BUY'
                signal_strength = min(abs(oi_change) / 5.0, 1.0)
            elif oi_change < -self.oi_threshold and price_change < 0:
                direction = 'SELL'
                signal_strength = min(abs(oi_change) / 5.0, 1.0)
            else:
                return None

            return {
                'token': token,
                'signal': round(signal_strength, 2),
                'direction': direction,
                'metadata': {
                    'oi_change_pct': round(oi_change, 2),
                    'price_change': round(float(price_change), 4)
                }
            }
        except Exception as e:
            cprint(f"Error generating signals: {e}", "red")
            return None
