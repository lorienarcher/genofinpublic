import pandas as pd
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning )
from backtesting import Backtest, Strategy
import numpy as np
from tqdm import tqdm
import pandas_ta as ta
import multiprocessing
from datetime import datetime
multiprocessing.set_start_method('fork')

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact cycle start and end dates replaced with generic placeholders
# ==========================================
CYCLE_START = '2019-04-02 00:00:00'
CYCLE_END = '2024-12-16 21:00:00'
MACRO_EVENT_DATE = '2024-04-19 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[CYCLE_START:CYCLE_END]

def generic_trend_indicator(close, length):
    """
    [SANITIZED] Replaced proprietary trend logic with a generic SMA placeholder.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class ValkyrieOptimizer(Strategy):
    # [SANITIZED] Proprietary parameters replaced with generic bounds for optimizer testing
    length = 10
    base_tp = 1.40
    macro_boost_tp = 1.70
    sl_pct = 0.97
    reentry_sl = 0.98
    l2_trigger = 1.03
    
    base_size = 0.2
    max_size = 0.4
    
    # Target variables for Walk-Forward Optimization
    profit_threshold = 0.20
    drawdown_limit = 0.80

    def init(self):
        self.trend_line = self.I(generic_trend_indicator, close=self.data.Close, length=self.length)
        self.equity_curve = [self.equity]
        self.entry_prices = [1]
        self.current_size = self.base_size

    def next(self):
        current_price = self.data.Close[-1]
        signal = self.trend_line
        
        signal_cur = 1 if current_price > signal[-1] else -1
        signal_prev = 1 if self.data.Close[-2] > signal[-2] else -1

        # --- L1 ENTRY ---
        if signal_cur > 0 > signal_prev and not self.position.is_long:
            high_series = pd.Series(self.data.High)
            low_series = pd.Series(self.data.Low)
            
            highest_high = high_series.max()
            highest_index = high_series.idxmax()
            slice_start = max(0, highest_index - 3)
            lowest_low = low_series.iloc[slice_start:].min()
            
            current_time = pd.Timestamp(str(self.data.index[-1]))
            macro_event = pd.Timestamp(MACRO_EVENT_DATE)
            
            active_tp = self.base_tp if macro_event > current_time else self.macro_boost_tp
            
            self.entry_prices.append(current_price)
            self.equity_curve.append(self.equity)
            
            # [SANITIZED] Exact sizing grid logic removed
            if highest_high * self.drawdown_limit > lowest_low:
                 self.current_size = min(self.max_size, self.current_size + 0.05)
            else:
                self.current_size = self.base_size

            self.buy(sl=self.entry_prices[-1] * self.sl_pct, tp=self.entry_prices[-1] * active_tp, size=self.current_size)

        # --- L2 RE-ENTRY ---
        elif signal_cur > 0 and self.entry_prices[-1] * 1.2 > current_price > self.entry_prices[-1] * self.l2_trigger and not self.position.is_long:
            current_time = pd.Timestamp(str(self.data.index[-1]))
            macro_event = pd.Timestamp(MACRO_EVENT_DATE)
            
            active_tp = self.base_tp if macro_event > current_time else self.macro_boost_tp
            
            self.buy(sl=self.entry_prices[-1] * self.reentry_sl, tp=self.entry_prices[-1] * active_tp, size=self.current_size)

        # --- BEAR EXIT ---
        elif signal_cur < 0 < signal_prev and not self.position.is_short:
            self.position.close()

# ==========================================
# WALK-FORWARD OPTIMIZATION WINDOWS
# ==========================================
iterations = [
    {'in_sample': [datetime(2019, 4, 1), datetime(2019, 10, 1)]},
    {'in_sample': [datetime(2019, 7, 1), datetime(2020, 1, 1)]},
    {'in_sample': [datetime(2019, 10, 2), datetime(2020, 4, 2)]},
    {'in_sample': [datetime(2020, 1, 2), datetime(2020, 7, 2)]},
    {'in_sample': [datetime(2020, 4, 3), datetime(2020, 10, 3)]},
    {'in_sample': [datetime(2020, 7, 3), datetime(2021, 1, 3)]},
    {'in_sample': [datetime(2020, 10, 4), datetime(2021, 4, 4)]},
    {'in_sample': [datetime(2022, 11, 10), datetime(2023, 5, 10)]},
    {'in_sample': [datetime(2023, 2, 10), datetime(2023, 8, 10)]},
    {'in_sample': [datetime(2023, 5, 11), datetime(2023, 11, 11)]},
    {'in_sample': [datetime(2023, 8, 11), datetime(2024, 2, 11)]},
    {'in_sample': [datetime(2023, 11, 12), datetime(2024, 5, 12)]},
    {'in_sample': [datetime(2024, 2, 12), datetime(2024, 8, 12)]},
    {'in_sample': [datetime(2024, 5, 13), datetime(2024, 11, 13)]},
    {'in_sample': [datetime(2024, 8, 13), datetime(2025, 4, 2)]}
]

report = []

# Iterative Walk-Forward Grid Search
for iter in tqdm(iterations):
    df_is = df[(df.index >= iter['in_sample'][0]) & (df.index <= iter['in_sample'][1])]
    bt_is = Backtest(df_is, ValkyrieOptimizer, cash=100_000_000, commission=.0005, exclusive_orders=True)
    
    stats_is, heatmap = bt_is.optimize(
        # [SANITIZED] Proprietary parameter search grids commented out to protect edge.
        # length=range(10, 15),
        # sl_pct=np.arange(0.95, 0.99, 0.01).tolist(),
        
        profit_threshold=np.arange(0.1, 0.3, 0.01).tolist(),
        drawdown_limit=np.arange(0.65, 0.90, 0.01).tolist(),
        
        maximize='Return [%]',
        method='grid',
        random_state=0,
        return_heatmap=True)
        
    report.append({
        'start_date': stats_is['Start'],
        'end_date': stats_is['End'],
        'heatmap_is': heatmap
    })

import matplotlib.pyplot as plt
import math
import seaborn as sns

plt.rcParams['figure.figsize'] = [40, 10]

rows = len(report)
for idx, res in enumerate(report):
    plt.subplot(math.ceil(rows / 2), math.ceil(rows / 2), idx + 1)
    plt.title(f"Iter # {idx + 1} - Year {res['start_date'].year}")

    # Create the heatmap
    heatmap = sns.heatmap(res['heatmap_is'].unstack())

    # Format x-axis tick labels
    x_ticks = heatmap.get_xticks()  
    x_labels = heatmap.get_xticklabels()  
    new_x_labels = [f"{float(label.get_text()):.3g}" for label in x_labels]  
    heatmap.set_xticklabels(new_x_labels)

    # Format y-axis tick labels
    y_ticks = heatmap.get_yticks()
    y_labels = heatmap.get_yticklabels()
    new_y_labels = [f"{float(label.get_text()):.3g}" for label in y_labels]
    heatmap.set_yticklabels(new_y_labels)

plt.show()
