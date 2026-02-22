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
# Exact historical cycle dates replaced with generic placeholders
# ==========================================
MACRO_START = '2015-07-10 00:00:00'
MACRO_END = '2024-12-21 00:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
# Resampling to a high timeframe (1W) for macro trend optimization
df = df.resample('1W').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[MACRO_START:MACRO_END]

def generic_macro_trend(close, length):
    """
    [SANITIZED] 
    Proprietary trend implementation removed.
    Replaced with a generic Simple Moving Average series to protect core signal alpha.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class MacroTrendOptimizer(Strategy):
    # [SANITIZED] Proprietary parameters replaced with generic bounds
    trend_length = 10
    base_size = 0.2

    def init(self):
        self.trend_line = self.I(generic_macro_trend, close=self.data.Close, length=self.trend_length)

    def next(self):
        signal = self.trend_line
        if len(signal) < 2:
            return
            
        current_price = self.data.Close[-1]
        
        signal_cur = 1 if current_price > signal[-1] else -1
        signal_prev = 1 if self.data.Close[-2] > signal[-2] else -1

        # --- MACRO BULL ENTRY ---
        if signal_cur > 0 > signal_prev and not self.position.is_long:
            self.buy(size=self.base_size)

        # --- MACRO BEAR EXIT ---
        elif signal_cur < 0 < signal_prev and not self.position.is_short:
            self.position.close()

from datetime import datetime
# ==========================================
# MACRO OPTIMIZATION WINDOW
# ==========================================
iterations = [
    # Full decade window for multi-cycle robustness testing
    {'in_sample': [datetime(2015, 7, 10), datetime(2024, 12, 20)]}
]

report = []

# Iterative Grid Search
for iter in tqdm(iterations):
    df_is = df[(df.index >= iter['in_sample'][0]) & (df.index <= iter['in_sample'][1])]
    bt_is = Backtest(df_is, MacroTrendOptimizer, cash=100_000_000, commission=.003, exclusive_orders=True, margin=1/10)
    
    stats_is, heatmap = bt_is.optimize(
        # [SANITIZED] Parameter search grids commented out to protect macro edge.
        # length=range(2, 4),
        # multiplier=np.arange(2.00, 2.6, 0.02).tolist(),
        
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
