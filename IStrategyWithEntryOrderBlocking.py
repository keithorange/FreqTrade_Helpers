from datetime import datetime, timedelta
import json
from typing import Optional
from freqtrade.strategy.interface import IStrategy
from pathlib import Path

import pandas as pd
from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

class IStrategyWithEntryOrderBlocking(IStrategy):
    max_open_trades_per_pair = 3  # Max number of concurrent trades per pair
    wait_time_after_trade = timedelta(minutes=60)  # 30 minutes wait time after a trade
    trade_count_file = Path("trade_counts.json")  # File to track trade counts

    def __init__(self):
        # Initialize trade counts from file if exists, else start with an empty dict
        if self.trade_count_file.exists():
            with open(self.trade_count_file, 'r') as f:
                self.trade_counts = json.load(f)
        else:
            self.trade_counts = {}

    def _update_trade_count(self, pair: str):
        """Updates the trade count for a given pair and saves to the file."""
        self.trade_counts[pair] = self.trade_counts.get(pair, 0) + 1
        with open(self.trade_count_file, 'w') as f:
            json.dump(self.trade_counts, f)

    def _can_open_trade(self, pair: str, current_time: datetime):
        """Checks if a new trade can be opened for the given pair."""
        if self.trade_counts.get(pair, 0) >= self.max_open_trades_per_pair:
            return False

        last_trade_time = self.trade_counts.get(f"{pair}_last_trade_time")
        if last_trade_time:
            last_trade_time = datetime.fromisoformat(last_trade_time)
            if current_time - last_trade_time < self.wait_time_after_trade:
                return False

        return True

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                            time_in_force: str, current_time: datetime, entry_tag: Optional[str] = None, side: str = 'long', **kwargs) -> bool:
        if not self._can_open_trade(pair, current_time):
            return False  # Abort trade if conditions are not met

        # Update trade count and last trade time
        self._update_trade_count(pair)
        self.trade_counts[f"{pair}_last_trade_time"] = current_time.isoformat()
        with open(self.trade_count_file, 'w') as f:
            json.dump(self.trade_counts, f)

        return True  # Confirm trade entry
