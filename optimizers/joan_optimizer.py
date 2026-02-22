import pandas as pd
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning )
from backtesting import Backtest, Strategy
import numpy as np
from tqdm import tqdm
import pandas_ta as ta
import multiprocessing
multiprocessing.set_start_method('fork')

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact cycle start and end dates replaced with generic placeholders
# ==========================================
CYCLE_START = '2015-01-01 00:00:00'
CYCLE_END = '2023-10-31 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('4H').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate().loc[CYCLE_START:CYCLE_END]

def generic_trend_indicator(close, length):
    """
    [SANITIZED] 
    Proprietary trend implementation removed.
    Replaced with a generic Simple Moving Average series to protect core signal alpha.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class JoanOptimizer(Strategy):
    # [SANITIZED] Proprietary parameters replaced with generic bounds
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
        
        signal_cur = 1 if current_price > signal[-1] else -1
        signal_prev = 1 if self.data.Close[-2] > signal[-2] else -1

        # --- BULL SIGNAL (Exit Short) ---
        if signal_cur > 0 > signal_prev and not self.position.is_long:
            self.position.close()

        # --- BEAR SIGNAL (Enter Laddered Short) ---
        elif signal_cur < 0 < signal_prev and not self.position.is_short:
            self.entry_prices.append(current_price)
            
            # [SANITIZED] Split-sizing formula removed. Retained structural logic.
            size_tier1 = self.base_size / 2
            size_tier2 = self.base_size / 2 
            
            self.sell(sl=current_price * self.sl_tier1, tp=current_price * self.tp_base, size=size_tier1)
            self.sell(sl=current_price * self.sl_tier2, tp=current_price * self.tp_base, size=size_tier2)

from datetime import datetime
# ==========================================
# WALK-FORWARD OPTIMIZATION WINDOWS
# ==========================================
iterations = [
    {'in_sample': [datetime(2017, 12, 1), datetime(2018, 6, 1)]},
    {'in_sample': [datetime(2018, 3, 2), datetime(2018, 9, 2)]},
    {'in_sample': [datetime(2018, 6, 3), datetime(2018, 12, 3)]},
    {'in_sample': [datetime(2018, 9, 4), datetime(2019, 4, 2)]},
    {'in_sample': [datetime(2021, 4, 1), datetime(2021, 10, 1)]},
    {'in_sample': [datetime(2021, 7, 2), datetime(2022, 1, 2)]},
    {'in_sample': [datetime(2021, 10, 3), datetime(2022, 4, 3)]},
    {'in_sample': [datetime(2022, 1, 4), datetime(2022, 7, 4)]},
    {'in_sample': [datetime(2022, 4, 10), datetime(2022, 11, 10)]}
]

report = []

# Iterative Walk-Forward Grid Search
for iter in tqdm(iterations):
    df_is = df[(df.index >= iter['in_sample'][0]) & (df.index <= iter['in_sample'][1])]
    bt_is = Backtest(df_is, JoanOptimizer, cash=100_000_000, commission=.0005, exclusive_orders=True, margin=1/10)
    stats_is, heatmap = bt_is.optimize(
        # [SANITIZED] Parameter search grids commented out to protect edge.
        # sls1=np.arange(1.040, 1.050, 0.002).tolist(),
        # tps1=np.arange(0.875, 0.876, 0.005).tolist(),
        
        maximize='Expectancy [%]',
        method='grid',
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
    new_x_labels = [f"{float(label.get_text()):.4g}" for label in x_labels]  
    heatmap.set_xticklabels(new_x_labels)

    # Format y-axis tick labels
    y_ticks = heatmap.get_yticks()
    y_labels = heatmap.get_yticklabels()
    new_y_labels = [f"{float(label.get_text()):.4g}" for label in y_labels]
    heatmap.set_yticklabels(new_y_labels)

plt.show()
