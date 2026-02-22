import pandas as pd
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning )
from backtesting import Backtest, Strategy
import numpy as np
import math
import pandas_ta as ta
import multiprocessing
from datetime import datetime
multiprocessing.set_start_method('fork')

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact historical cycle dates replaced with generic placeholders
# ==========================================
MACRO_START = '2015-01-01 00:00:00'
MACRO_END = '2021-04-01 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('1D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[MACRO_START:MACRO_END]

def generic_macro_trend(close, length):
    """
    [SANITIZED] 
    Proprietary AlphaTrend calculation combining ATR, RSI, and custom trailing logic removed.
    Replaced with a generic Simple Moving Average to protect core signal generation.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class AlphaMacroBacktest(Strategy):
    # [SANITIZED] Proprietary trend parameters removed
    trend_length = 20
    base_size = 0.1

    def init(self):
        self.trend_line = self.I(generic_macro_trend, close=self.data.Close, length=self.trend_length)
        self.buy_signal = False
        self.sell_signal = False

    def next(self):
        signal = self.trend_line
        if len(signal) < 3:
            return
        
        signal_cur = signal[-1]
        signal_prev = signal[-2]
        signal_prev2 = signal[-3]

        # Generic momentum crossover signals
        self.buy_signal = (signal_cur > signal_prev) and (signal_prev <= signal_prev2)
        self.sell_signal = (signal_cur < signal_prev) and (signal_prev >= signal_prev2)

        # --- MACRO BULL ENTRY ---
        if self.buy_signal and not self.position.is_long:
            self.buy(size=self.base_size)

        # --- MACRO BEAR EXIT ---
        elif self.sell_signal and not self.position.is_short:
            self.position.close()

bt = Backtest(df, AlphaMacroBacktest, cash=100_000_000, commission=.0005, exclusive_orders=True, margin=1 / 10)

stats = bt.run()
print(stats)
bt.plot()
