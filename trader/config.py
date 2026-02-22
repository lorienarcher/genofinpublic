# --- START OF FILE config_example.py ---
# ======================================================================================================================
# API INTEGRATIONS (Keys are assumed present, no inline validation required)
# ======================================================================================================================
binance_copy_key = "YOUR_BINANCE_KEY"
binance_copy_secret = "YOUR_BINANCE_SECRET"

# BITMEX
bitmex_copy_key = "YOUR_BITMEX_KEY"
bitmex_copy_secret = "YOUR_BITMEX_SECRET"

# OKX
okx_copy_key = "YOUR_OKX_KEY"
okx_copy_secret = "YOUR_OKX_SECRET"
okx_copy_pass = "YOUR_OKX_PASSWORD" 

# SLACK NOTIFICATIONS
slack_token = "YOUR_SLACK_TOKEN"
slack_channel = "YOUR_SLACK_CHANNEL"

# ======================================================================================================================
# GLOBAL SETTINGS
# ======================================================================================================================
symbol_name = "btc"
timeframe = "4h"
rsi_timeframe = "1d"
percentage_of_capital = int(99) 

# ======================================================================================================================
# [SANITIZED] VALKYRIE & RSI STRATEGY PARAMETERS
# Proprietary trend multipliers, drawdown thresholds, and scale-in tiers removed.
# ======================================================================================================================
length = int(10)          
multiplier = float(0.00)  
rsi_length = int(6)       

sll1 = float(0.000)       
tpl = float(0.000)        
h1_close = float(0.000)   
h2_sl = float(0.000)      
rsi_threshold = int(0)    

max_leverage = int(10)    
min_leverage = int(1)     

profit_threshold = float(0.00)   
drawdown_threshold = float(0.00) 

# ======================================================================================================================
# [SANITIZED] HIGH VOLATILITY (HV) PARAMETERS
# Proprietary multi-tier volatility matrix removed.
# ======================================================================================================================
hv_lr = float(0.000)    
hv_sl = float(0.000)    
hv_lr2 = float(0.000)   
hv_sl2 = float(0.000)   
hv_tp = float(0.00)
