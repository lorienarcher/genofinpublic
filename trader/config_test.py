# --- START OF FILE config_test_example.py ---
# ======================================================================================================================
# API INTEGRATIONS (Testnet Environment)
# ======================================================================================================================
binance_test_key = "YOUR_BINANCE_TEST_KEY"
binance_test_secret = "YOUR_BINANCE_TEST_SECRET"

# BITMEX
bitmex_test_key = "YOUR_BITMEX_TEST_KEY"
bitmex_test_secret = "YOUR_BITMEX_TEST_SECRET"

# OKX
okx_test_key = "YOUR_OKX_TEST_KEY"
okx_test_secret = "YOUR_OKX_TEST_SECRET"
okx_test_pass = "YOUR_OKX_TEST_PASSWORD" 

# SLACK NOTIFICATIONS
slack_token = "YOUR_SLACK_TOKEN"
slack_channel = "YOUR_SLACK_CHANNEL"

# ======================================================================================================================
# GLOBAL SETTINGS
# ======================================================================================================================
symbol_name = "btc"
timeframe = "5m"
rsi_timeframe = "15m"
percentage_of_capital = int(99)   

# ======================================================================================================================
# [SANITIZED] VALKYRIE & RSI STRATEGY PARAMETERS
# Proprietary trend multipliers and scale-in tiers removed for public repository.
# ======================================================================================================================
length = int(0)          
multiplier = float(0.0)  
rsi_length = int(0)       

sll1 = float(0.000)       
tpl = float(0.000)        
h1_close = float(0.0000)   
h2_sl = float(0.0000)      
rsi_threshold = int(0)    

max_leverage = int(10)    
min_leverage = int(1)     

profit_threshold = float(0.000)   
drawdown_threshold = float(0.000) 

# ======================================================================================================================
# [SANITIZED] HIGH VOLATILITY (HV) PARAMETERS
# Proprietary multi-tier volatility matrix removed.
# ======================================================================================================================
hv_lr = float(0.000)    
hv_sl = float(0.000)    
hv_lr2 = float(0.00)   
hv_sl2 = float(0.000)   
hv_tp = float(0.000)
