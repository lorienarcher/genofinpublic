import pandas as pd
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning )
from backtesting import Backtest, Strategy
import pandas_ta as ta
import multiprocessing
from datetime import datetime
multiprocessing.set_start_method('fork')

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact historical cycle and halving dates replaced with generic placeholders
# ==========================================
MACRO_START = '2015-01-01 00:00:00'
MACRO_END = '2024-12-31 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
# Resampling to a high timeframe (1D) for macro trend detection
df = df.resample('1D').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[MACRO_START:MACRO_END]

def generic_macro_trend(close, length):
    """
    [SANITIZED] 
    Proprietary macro trend indicator removed.
    Replaced with a generic high-timeframe Simple Moving Average to protect core directional alpha.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class MacroTrendBacktest(Strategy):
    # [SANITIZED] Proprietary trend parameters and precise portfolio sizing removed
    trend_length = 20
    base_size = 0.2

    def init(self):
        self.trend_line = self.I(generic_macro_trend, close=self.data.Close, length=self.trend_length)

    def next(self):
        signal = self.trend_line
        if len(signal) < 2:
            return
            
        current_price = self.data.Close[-1]
        
        # Generic trend logic simulating directional +1 / -1 signals
        signal_cur = 1 if current_price > signal[-1] else -1
        signal_prev = 1 if self.data.Close[-2] > signal[-2] else -1

        # --- MACRO BULL ENTRY ---
        if signal_cur > 0 > signal_prev and not self.position.is_long:
            self.buy(size=self.base_size)

        # --- MACRO BEAR EXIT ---
        elif signal_cur < 0 < signal_prev and not self.position.is_short:
            self.position.close()

bt = Backtest(df, MacroTrendBacktest, cash=100_000_000, commission=.003, exclusive_orders=True, margin=1/10)
stats = bt.run()
print(stats)
bt.plot()
