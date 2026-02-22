import pandas as pd
from backtesting import Backtest, Strategy
import pandas_ta as ta
from datetime import datetime

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact Bitcoin cycle and halving dates replaced with generic placeholders
# ==========================================
CYCLE_START = '2022-01-01 00:00:00'
CYCLE_END = '2026-01-01 00:00:00'
MACRO_EVENT_DATE = '2024-04-19 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[CYCLE_START:CYCLE_END]

def generic_trend_indicator(close, length):
    """
    [SANITIZED] Replaced proprietary Supertrend with a generic Simple Moving Average
    to protect the core directional alpha.
    """
    return ta.sma(close=close, length=length).to_numpy()

class TrendBacktest(Strategy):
    # [SANITIZED] Proprietary risk, dynamic sizing, and exact TP/SL parameters removed
    trend_length = 10
    base_tp = 1.10
    macro_boost_tp = 1.20
    sl_pct = 0.95
    reentry_sl = 0.98
    
    base_size = 0.1
    max_size = 0.3
    drawdown_limit = 0.8

    def init(self):
        self.trend_line = self.I(generic_trend_indicator, close=pd.Series(self.data.Close), length=self.trend_length)
        self.equity_curve = [self.equity]
        self.entry_prices = [1]
        self.current_size = self.base_size

    def next(self):
        current_price = self.data.Close[-1]
        
        # Generic trend logic simulating directional +1 / -1 signals
        signal_cur = 1 if current_price > self.trend_line[-1] else -1
        signal_prev = 1 if self.data.Close[-2] > self.trend_line[-2] else -1

        # --- BULL SIGNAL ---
        if signal_cur > 0 > signal_prev and not self.position.is_long:
            high_series = pd.Series(self.data.High)
            low_series = pd.Series(self.data.Low)

            highest_high = high_series.max()
            highest_idx = high_series.argmax()
            slice_start = max(0, highest_idx - 3)
            lowest_low = low_series.iloc[slice_start:].min()

            self.entry_prices.append(current_price)
            self.equity_curve.append(self.equity)

            # [SANITIZED] Proprietary equity recovery sizing math removed. 
            # Replaced with a simplified placeholder to maintain the structural 
            # demonstration of dynamic quantitative risk management.
            if highest_high * self.drawdown_limit > lowest_low:
                self.current_size = min(self.max_size, self.current_size + 0.05)
            else:
                self.current_size = self.base_size

            # Demonstrate macro-driven structure (Event adaptation)
            current_time = self.data.index[-1]
            macro_event = pd.Timestamp(MACRO_EVENT_DATE)

            if macro_event > current_time:
                active_tp = self.base_tp
            else:
                active_tp = self.macro_boost_tp

            self.buy(sl=current_price * self.sl_pct, tp=current_price * active_tp, size=self.current_size)
            print(f"Size: {self.current_size}")

        # --- L2 RE-ENTRY ---
        elif signal_cur > 0 and self.entry_prices[-1] * 1.2 > current_price > self.entry_prices[-1] * 1.05 and not self.position.is_long:
            current_time = pd.Timestamp(str(self.data.index[-1]))
            macro_event = pd.Timestamp(MACRO_EVENT_DATE)
            
            if macro_event > current_time:
                active_tp = self.base_tp
            else:
                active_tp = self.macro_boost_tp
                
            self.buy(sl=self.entry_prices[-1] * self.reentry_sl, tp=self.entry_prices[-1] * active_tp, size=self.current_size)
            print(f"Size: {self.current_size}")

        # --- BEAR SIGNAL ---
        elif signal_cur < 0 < signal_prev and not self.position.is_short:
            self.position.close()


bt = Backtest(df, TrendBacktest, cash=100_000_000, commission=.003, exclusive_orders=True, margin=1/10)

stats = bt.run()
print(stats)

# Browser Plotting Logic
import webbrowser

filename = f"Trend_Backtest_Sanitized.html"
bt.plot(filename=filename, open_browser=False)

brave_path = "open -a /Applications/Brave\\ Browser.app %s"
webbrowser.get(brave_path).open(filename)
