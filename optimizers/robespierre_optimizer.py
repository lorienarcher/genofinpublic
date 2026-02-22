import pandas as pd
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning )
from backtesting import Backtest, Strategy
import numpy as np
from tqdm import tqdm
import pandas_ta as ta
import multiprocessing
import math
from datetime import datetime
multiprocessing.set_start_method('fork')

# ==========================================
# [SANITIZED] PROPRIETARY MACRO TIMELINES
# Exact historical cycle dates replaced with generic placeholders
# ==========================================
CYCLE_START = '2019-04-02 00:00:00'
CYCLE_END = '2025-10-16 21:00:00'

df = pd.read_csv('../data/btc_usdt_1m.csv', index_col='Time', parse_dates=True)
df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
df = df.interpolate()
df = df.loc[CYCLE_START:CYCLE_END]

def generic_trend_indicator(close, length):
    """
    [SANITIZED] 
    Proprietary AlphaTrend math removed.
    Replaced with a generic Simple Moving Average series to protect core signal alpha.
    """
    return ta.sma(close=pd.Series(close), length=length).to_numpy()

class RobespierreOptimizer(Strategy):
    # [SANITIZED] Proprietary multipliers replaced with generic bounds for testing
    length = 11
    base_tp = 1.50
    sl_pct = 0.95
    base_size = 0.3

    def init(self):
        self.trend_line = self.I(generic_trend_indicator, close=self.data.Close, length=self.length)
        self.buy_signal = False
        self.sell_signal = False
        self.equity_curve = [self.equity]
        self.current_size = self.base_size

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
        if self.buy_signal and not self.position.is_long:
            self.equity_curve.append(self.equity)
            
            # [SANITIZED] Proprietary sizing recovery math removed. 
            # Replaced with basic directional scaling structure.
            if self.equity_curve[-1] > self.equity_curve[-2]:
                self.current_size = max(self.base_size, self.current_size - 0.1)
            elif self.equity_curve[-1] < self.equity_curve[-2]:
                self.current_size = min(0.99, self.current_size + 0.1)

            self.buy(sl=current_price * self.sl_pct, tp=current_price * self.base_tp, size=self.current_size)

        # --- L1 EXIT ---
        elif self.sell_signal and self.position.is_long:
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
    bt_is = Backtest(df_is, RobespierreOptimizer, cash=100_000_000, commission=.003, exclusive_orders=True, margin=1/10)
    
    stats_is, heatmap = bt_is.optimize(
        # [SANITIZED] Proprietary parameter search grids commented out to protect edge.
        # sl_pct=np.arange(0.94, 0.95, 0.002).tolist(),
        # base_tp=np.arange(1.50, 1.60, 0.01).tolist(),
        
        maximize='Expectancy [%]',
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
