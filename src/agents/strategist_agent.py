"""
🌙 Moon Dev's Strategist Agent
Searches the web for trending trading strategy ideas and proposes new strategies
based on current market conditions.
"""

import os
import json
import requests
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
import anthropic

from src.config import MONITORED_TOKENS
from src import nice_funcs as n

# Prompt for strategy generation
GENERATE_STRATEGY_PROMPT = """
You are Moon Dev's Strategist AI 🌙

Trending Strategy Ideas:
{ideas}

Current Market Snapshot:
{market_data}

Using these ideas and market conditions, write a new trading strategy in Python.
The strategy must inherit from `BaseStrategy` and implement `generate_signals()`.
Include basic risk management such as stop loss and take profit levels.
Respond ONLY with the Python code for the strategy.
"""

class StrategistAgent:
    """Agent that searches the web and creates strategy code"""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_KEY missing")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _reddit_titles(self, sort: str, limit: int):
        """Helper to fetch titles from Reddit"""
        url = f"https://www.reddit.com/r/algotrading/{sort}.json?limit={limit}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [c["data"]["title"] for c in data.get("data", {}).get("children", [])]
        return []

    def _hn_titles(self, limit: int):
        """Fetch titles from HackerNews related to trading"""
        url = f"https://hn.algolia.com/api/v1/search?query=trading%20strategy&tags=story&hitsPerPage={limit}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [hit.get("title", "") for hit in data.get("hits", [])]
        return []

    def search_trending_strategies(self, limit: int = 5):
        """Combine ideas from multiple sources"""
        titles = []
        try:
            titles.extend(self._reddit_titles("new", limit))
            titles.extend(self._reddit_titles("top", limit))
            titles.extend(self._hn_titles(limit))
        except Exception as e:
            cprint(f"Error fetching ideas: {e}", "red")
        return titles

    def get_market_snapshot(self):
        """Collect simple market data for monitored tokens"""
        snapshot = {}
        for token in MONITORED_TOKENS:
            df = n.get_data(token, days_back_4_data=1, timeframe="1H")
            if df is None or df.empty:
                continue
            snapshot[token] = {
                "last_close": df["Close"].iloc[-1],
                "ma20": df["MA20"].iloc[-1],
                "rsi": df["RSI"].iloc[-1],
                "change_24h_pct": ((df["Close"].iloc[-1] - df["Close"].iloc[-24]) / df["Close"].iloc[-24]) * 100 if len(df) >= 24 else 0,
            }
        return snapshot

    def create_strategy(self):
        """Generate new strategy code using an LLM"""
        ideas = self.search_trending_strategies()
        market_data = self.get_market_snapshot()
        prompt = GENERATE_STRATEGY_PROMPT.format(
            ideas=json.dumps(ideas, indent=2),
            market_data=json.dumps(market_data, indent=2)
        )
        message = self.client.messages.create(
            model=os.getenv("AI_MODEL", "claude-3-haiku-20240307"),
            max_tokens=800,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        response = message.content
        if isinstance(response, list):
            response = response[0].text if hasattr(response[0], "text") else str(response[0])
        return response

