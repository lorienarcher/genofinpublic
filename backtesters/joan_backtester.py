import pandas as pd
from backtesting import Backtest, Strategy
import pandas_ta as ta
import multiprocessing
multiprocessing.set_start_method('fork')

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact historical cycle start and end dates replaced with generic placeholders
# ==========================================
CYCLE_START = '2021-04-01 00:00:00'
CYCLE_END = '2022-11-11 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('4H').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[CYCLE_START:CYCLE_END]

def generic_trend_indicator(close, length):
    """
    [SANITIZED] 
    Proprietary trend implementation removed.
    Replaced with a generic Simple Moving Average series to protect core signal alpha.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class JoanBacktest(Strategy):
    # [SANITIZED] Proprietary risk parameters and fractional sizing math removed
    trend_length = 7
    sl_tier1 = 1.02
    sl_tier2 = 1.05
    tp_base = 0.90
    base_size = 0.3

    def init(self):
        self.trend_line = self.I(generic_trend_indicator, close=self.data.Close, length=self.trend_length)
        self.entry_prices = [1]

    def next(self):
        signal = self.trend_line
        if len(signal) < 2:
            return

        current_price = self.data.Close[-1]
        
        # Generic trend logic simulating directional +1 / -1 signals
        signal_cur = 1 if current_price > signal[-1] else -1
        signal_prev = 1 if self.data.Close[-2] > signal[-2] else -1

        # --- BULL SIGNAL (Exit Short) ---
        if signal_cur > 0 > signal_prev and not self.position.is_long:
            self.position.close()

        # --- BEAR SIGNAL (Enter Laddered Short) ---
        elif signal_cur < 0 < signal_prev and not self.position.is_short:
            self.entry_prices.append(current_price)
            
            # [SANITIZED] Proprietary split-sizing formula removed.
            # Retained structural logic of laddered stops on a single entry trigger.
            size_tier1 = self.base_size / 2
            size_tier2 = self.base_size / 2 
            
            self.sell(sl=current_price * self.sl_tier1, tp=current_price * self.tp_base, size=size_tier1)
            self.sell(sl=current_price * self.sl_tier2, tp=current_price * self.tp_base, size=size_tier2)

bt = Backtest(df, JoanBacktest, cash=100_000_000, commission=.003, exclusive_orders=True, margin=0.1)

stats = bt.run()
bt.plot()
print(stats)
