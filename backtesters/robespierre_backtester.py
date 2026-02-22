import pandas as pd
from backtesting import Backtest, Strategy
import pandas_ta as ta
import numpy as np
import math
from datetime import datetime

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact Bitcoin cycle and halving dates replaced with generic placeholders
# ==========================================
CYCLE_START = '2015-07-10 00:00:00'
CYCLE_END = '2025-10-01 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[CYCLE_START:CYCLE_END]

def generic_trend_indicator(close, length):
    """
    [SANITIZED] 
    Proprietary AlphaTrend mathematical implementation (ATR + RSI trailing logic) removed.
    Replaced with a generic Simple Moving Average series to protect core signal alpha.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class RobespierreBacktest(Strategy):
    # [SANITIZED] Proprietary risk, dynamic sizing, and exact TP/SL parameters removed
    length = 11
    base_tp = 1.50
    sl_pct = 0.97
    reentry_sl = 0.98
    l2_trigger = 1.035
    
    base_size = 0.1
    max_size = 0.3

    def init(self):
        self.trend_line = self.I(generic_trend_indicator, close=self.data.Close, length=self.length)
        self.buy_signal = False
        self.sell_signal = False
        self.equity_curve = [self.equity]
        self.entry_prices = [0]
        self.current_size = self.base_size
        self.uptrend = False

    def next(self):
        signal = self.trend_line
        if len(signal) < 3:
            return
        
        current_price = self.data.Close[-1]
        signal_cur = signal[-1]
        signal_prev = signal[-2]
        signal_prev2 = signal[-3]

        # Generic momentum crossover signals
        self.buy_signal = (signal_cur > signal_prev) and (signal_prev <= signal_prev2)
        self.sell_signal = (signal_cur < signal_prev) and (signal_prev >= signal_prev2)

        # --- L1 ENTRY ---
        if self.buy_signal and not self.position.is_long and not self.uptrend:
            self.uptrend = True
            high_series = pd.Series(self.data.High)
            low_series = pd.Series(self.data.Low)
            
            highest_high = high_series.max()
            highest_index = high_series.idxmax()
            slice_start = max(0, highest_index - 3)
            lowest_low = low_series.iloc[slice_start:].min()
            
            self.entry_prices.append(current_price)
            self.equity_curve.append(self.equity)
            
            # [SANITIZED] Proprietary equity recovery sizing math removed.
            # Replaced with basic scaling mechanism to demonstrate risk management infrastructure.
            if highest_high * 0.80 > lowest_low:
                 self.current_size = min(self.max_size, self.current_size + 0.05)
            else:
                self.current_size = self.base_size

            self.buy(sl=self.entry_prices[-1] * self.sl_pct, tp=self.entry_prices[-1] * self.base_tp, size=self.current_size)

        # --- L2 RE-ENTRY ---
        elif self.entry_prices[-1] * 1.2 > current_price > self.entry_prices[-1] * self.l2_trigger and not self.position.is_long and self.uptrend:
            self.buy(sl=self.entry_prices[-1] * self.reentry_sl, tp=self.entry_prices[-1] * self.base_tp, size=self.current_size)

        # --- BEAR SIGNAL ---
        elif self.sell_signal and not self.position.is_short:
            self.uptrend = False
            self.position.close()

bt = Backtest(df, RobespierreBacktest, cash=100_000_000, commission=.0005, exclusive_orders=True, margin=1/10)

stats = bt.run()
print(stats)
bt.plot()
