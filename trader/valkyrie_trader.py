import sys
from time import sleep
import pandas as pd
import traceback
import logging
import time
import json
import threading
from collections import deque
import websocket
import config
import config_test
from genofinlib import ws_manager, order_manager, helpers, slave_manager
from genofinlib.slack_bot import StrategyState, trade_message, error_message, info_message

# =========================
# CONFIG SELECTION
# =========================
IS_TESTNET = True  # <--- TOGGLE THIS ONLY

if IS_TESTNET:
    logging.info("--- RUNNING IN TESTNET MODE ---")
    info_message("--- RUNNING IN TESTNET MODE ---", StrategyState.VK)

    # 1. Select the Config File
    cfg = config_test

    # 2. Select URLs
    WS_API_URL = "wss://testnet.binancefuture.com/ws-fapi/v1"
    FSTREAM_URL = "wss://stream.binancefuture.com/ws"
    BINANCE_FAPI_URL = "https://testnet.binancefuture.com"

    # 3. Select API Keys (Directly accessed, no verification needed)
    BINANCE_API_KEY = cfg.binance_test_key
    BINANCE_API_SECRET = cfg.binance_test_secret

else:
    logging.info("--- RUNNING IN REAL MONEY MODE ---")
    info_message("--- RUNNING IN REAL MONEY MODE ---", StrategyState.VK)

    # 1. Select the Config File
    cfg = config

    # 2. Select URLs
    WS_API_URL = "wss://ws-fapi.binance.com/ws-fapi/v1"
    FSTREAM_URL = "wss://fstream.binance.com/ws"
    BINANCE_FAPI_URL = "https://fapi.binance.com"

    # 3. Select API Keys (Directly accessed, no verification needed)
    BINANCE_API_KEY = cfg.binance_copy_key
    BINANCE_API_SECRET = cfg.binance_copy_secret

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
MAX_BARS = 1500
ohlcv_buffer = deque(maxlen=MAX_BARS)
ohlcv_lock = threading.Lock()

# --- CONSTANTS FROM CONFIG ---
SYMBOL_NAME = cfg.symbol_name.upper()
SYMBOL = f"{SYMBOL_NAME}/USDT"
logging.info(f"SYMBOL: {SYMBOL}")
info_message(f"SYMBOL = {SYMBOL}", StrategyState.VK)

TIMEFRAME = cfg.timeframe
logging.info(f"TIMEFRAME: {TIMEFRAME}")
info_message(f"TIMEFRAME = {TIMEFRAME}", StrategyState.VK)

PERCENTAGE_OF_CAPITAL = cfg.percentage_of_capital
logging.info(f"PERCENTAGE_OF_CAPITAL = {PERCENTAGE_OF_CAPITAL}")
info_message(f"PERCENTAGE_OF_CAPITAL = {PERCENTAGE_OF_CAPITAL}", StrategyState.VK)

sleep(2) 

# [SANITIZED] Generic params replacing proprietary trend/volatility variables
GENERIC_FAST_MA = getattr(cfg, 'fast_ma', 10)
logging.info(f"GENERIC_FAST_MA = {GENERIC_FAST_MA}")
info_message(f"GENERIC_FAST_MA = {GENERIC_FAST_MA}", StrategyState.ST)

GENERIC_SLOW_MA = getattr(cfg, 'slow_ma', 50)
logging.info(f"GENERIC_SLOW_MA = {GENERIC_SLOW_MA}")
info_message(f"GENERIC_SLOW_MA = {GENERIC_SLOW_MA}",StrategyState.ST)

SLL1 = cfg.sll1
logging.info(f"SLL1 = {SLL1}")
info_message(f"SLL1 = {SLL1}", StrategyState.ST)

TPL = cfg.tpl
logging.info(f"TPL = {TPL}")
info_message(f"TPL = {TPL}", StrategyState.ST)

H1_CLOSE = cfg.h1_close
logging.info(f"H1_CLOSE = {H1_CLOSE}")
info_message(f"H1_CLOSE = {H1_CLOSE}", StrategyState.ST)

H2_SL = cfg.h2_sl
logging.info(f"H2_SL = {H2_SL}")
info_message(f"H2_SL = {H2_SL}", StrategyState.ST)

MAX_LEVERAGE = cfg.max_leverage
logging.info(f"MAX_LEVERAGE = {MAX_LEVERAGE}")
info_message(f"MAX_LEVERAGE = {MAX_LEVERAGE}", StrategyState.ST)

MIN_LEVERAGE = cfg.min_leverage
logging.info(f"MIN_LEVERAGE = {MIN_LEVERAGE}")
info_message(f"MIN_LEVERAGE = {MIN_LEVERAGE}", StrategyState.ST)

PROFIT_THRESHOLD = cfg.profit_threshold
logging.info(f"PROFIT_THRESHOLD = {PROFIT_THRESHOLD}")
info_message(f"PROFIT_THRESHOLD = {PROFIT_THRESHOLD}", StrategyState.ST)

DRAWDOWN_THRESHOLD = cfg.drawdown_threshold
logging.info(f"DRAWDOWN_THRESHOLD = {DRAWDOWN_THRESHOLD}")
info_message(f"DRAWDOWN_THRESHOLD = {DRAWDOWN_THRESHOLD}", StrategyState.ST)

sleep(2)

# =========================
# INITIALIZATION
# =========================
# 1. Start Slaves (CCXT Free)
slaves = slave_manager.SlaveManager(cfg, IS_TESTNET)

# 2. Start WebSocket Manager
ws_api = ws_manager.WebSocketApiManager(
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    WS_API_URL,
    IS_TESTNET
)
ws_api.connect()

# 3. Start OrderManager (Now acts as the unified Binance Client)
executor = order_manager.OrderManager(
    ws_api=ws_api,
    symbol=SYMBOL,
    api_key=BINANCE_API_KEY,
    api_secret=BINANCE_API_SECRET,
    is_testnet=IS_TESTNET
)

# 4. Alias executor to 'exchange' so your main loop runs without modifications
exchange = executor
exchange.load_markets()

# =========================
# STATE
# =========================
# Common State
in_long = False
in_position = False
active_strategy = None  # Values: "TREND", "SCALP", "HV"

sleep(2)

# Strategy 1 State
failed_l1 = False
l2_order = False
take_profit = False
trend_up = False
trend_down = False
leveragenum = cfg.min_leverage
entry_price_list = [112900, 113752, 113648, 92589, 91192]

sleep(2)

# Strategy 2 State
scalp_long = False
adaptabletp = False
tp_is_boosted = False
scalp_entry_list = [31]

sleep(2)

# HV State
bar_time_prev = None
is_bar_closed = False
sl_hv_triggered = False
hv_traded_bar = None


# =========================
# WEBSOCKET STREAMS
# =========================
def on_user_message(ws, msg):
    try:
        data = json.loads(msg)
        if data.get("e") == "ORDER_TRADE_UPDATE":
            o = data.get("o", {})
            if o.get("X") != "FILLED": return
            cid = o.get("c", "")
            logging.info(f"[WS] FILL: {cid}")

            global failed_l1, take_profit, l2_order, sl_hv_triggered, active_strategy

            # --- STOP LOSS HIT ---
            if "SL" in cid:
                trade_message(f"STOP LOSS triggered ({active_strategy})", StrategyState.VK)

                # *** SLAVE ACTION: CLOSE POSITIONS ***
                logging.info("Master SL Hit -> Closing Slaves")
                slaves.exit_long()
                # *************************************

                # Logic Router
                if active_strategy == "HV":
                    sl_hv_triggered = True

                elif active_strategy in ["TREND", "SCALP"]:
                    failed_l1 = True
                    take_profit = False
                    l2_order = False

            # --- TAKE PROFIT HIT ---
            elif "TP" in cid:
                trade_message(f"TAKE PROFIT triggered ({active_strategy})", StrategyState.VK)

                # *** SLAVE ACTION: CLOSE POSITIONS ***
                logging.info("Master TP Hit -> Closing Slaves")
                slaves.exit_long()
                # *************************************

                if active_strategy in ["TREND", "SCALP"]:
                    failed_l1 = False
                    take_profit = True
                    l2_order = False

    except:
        pass


def start_user_socket():
    while True:
        try:
            lk = helpers.get_listen_key(BINANCE_API_KEY, BINANCE_FAPI_URL)
            ws = websocket.WebSocketApp(f"{FSTREAM_URL}/{lk}", on_message=on_user_message)
            ws.run_forever()
        except:
            time.sleep(5)


def on_kline_message(ws, message):
    try:
        data = json.loads(message)
        if "k" not in data: return
        k = data["k"]
        candle = [int(k["t"]), float(k["o"]), float(k["h"]), float(k["l"]), float(k["c"]), float(k["v"])]
        with ohlcv_lock:
            if k["x"]:
                ohlcv_buffer.append(candle)
            else:
                if len(ohlcv_buffer) > 0: ohlcv_buffer[-1] = candle
    except:
        pass


def start_kline_socket():
    while True:
        try:
            ws = websocket.WebSocketApp(f"{FSTREAM_URL}/{SYMBOL_NAME.lower()}usdt@kline_{TIMEFRAME}",
                                        on_message=on_kline_message)
            ws.run_forever()
        except:
            time.sleep(5)


def warmup_ohlcv():
    bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=MAX_BARS)
    with ohlcv_lock:
        ohlcv_buffer.clear()
        for b in bars: ohlcv_buffer.append(b)


# Start Threads
warmup_ohlcv()
threading.Thread(target=start_kline_socket, daemon=True).start()
threading.Thread(target=start_user_socket, daemon=True).start()
threading.Thread(target=helpers.keep_alive_listen_key, args=(BINANCE_API_KEY, BINANCE_FAPI_URL),
                 daemon=True).start()

# =========================
# MAIN LOOP
# =========================
logging.info("Multi-Strategy Bot Started (Public Version)...")
info_message("Multi-Strategy Bot Started (Public Version)...", StrategyState.VK)

while True:
    try:
        # 1. State Update (Single API Call)
        account_data = exchange.fetch_balance()['info']

        free_balance = float(account_data.get('availableBalance', 0.0))
        positions = account_data.get('positions', [])

        cur_pos = [p for p in positions if p['symbol'] == SYMBOL_NAME + "USDT" and float(p['positionAmt']) != 0]

        in_position = len(cur_pos) > 0
        in_long = in_position and float(cur_pos[0]['positionAmt']) > 0

        if not in_position:
            # Reset All States when flat
            executor.active_tp_id = None
            active_strategy = None

            scalp_long = False
            adaptabletp = False
            tp_is_boosted = False

            if not sl_hv_triggered:
                hv_in_long = False

        # 2. Process Data
        with ohlcv_lock:
            if len(ohlcv_buffer) < 100:
                time.sleep(1)
                continue
            bars = list(ohlcv_buffer)

        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # ==========================================
        # [SANITIZED] PROPRIETARY INDICATORS REMOVED
        # Replaced with generic Moving Averages and Volume metrics
        # ==========================================
        df['sma_fast'] = df['close'].rolling(window=GENERIC_FAST_MA).mean()
        df['sma_slow'] = df['close'].rolling(window=GENERIC_SLOW_MA).mean()
        df['vol_sma'] = df['volume'].rolling(window=20).mean()

        current_price = float(df["close"].iloc[-1])
        highest_high = df['high'].max()
        lowest_low = df['low'][df['high'].idxmax() - 3:].min()

        sma_fast_cur = df['sma_fast'].iloc[-2]
        sma_slow_cur = df['sma_slow'].iloc[-2]
        sma_fast_prev = df['sma_fast'].iloc[-3]
        sma_slow_prev = df['sma_slow'].iloc[-3]

        # Generic Trend Signal (1 = Bullish, -1 = Bearish)
        signal_cur = 1 if sma_fast_cur > sma_slow_cur else -1
        signal_prev = 1 if sma_fast_prev > sma_slow_prev else -1

        # Generic Scalp Metric (Price dips > 5% below slow MA)
        is_scalp_territory = current_price < (df['sma_slow'].iloc[-1] * 0.95)

        # Generic HV Metric (Volume spike > 2x average)
        volatility_spike = df['volume'].iloc[-1] > (df['vol_sma'].iloc[-1] * 2)

        candle_curr = ohlcv_buffer[-1]
        hv_open = candle_curr[1]
        hv_last_price = candle_curr[4]

        bar_time_cur = candle_curr[0]
        if bar_time_prev is not None and bar_time_prev != bar_time_cur:
            is_bar_closed = True
        else:
            is_bar_closed = False
        bar_time_prev = bar_time_cur

        logging.info("========== STRATEGY STATE ==========")
        logging.info("sma_fast: %.2f", df['sma_fast'].iloc[-1])
        logging.info("sma_slow: %.2f", df['sma_slow'].iloc[-1])
        logging.info("signal_check (trend): %s", signal_cur)
        logging.info("scalp_territory: %s", is_scalp_territory)
        
        logging.info("failed_l1: %s", failed_l1)
        logging.info("take_profit: %s", take_profit)
        logging.info("scalp_long: %s", scalp_long)

        # ==============================================================================
        # STRATEGY LOGIC ROUTER
        # ==============================================================================

        # ------------------------------------
        # STRATEGY 1: GENERIC TREND (Replacing ST)
        # ------------------------------------
        if (signal_cur > 0 > signal_prev and not failed_l1 and not trend_up):
            trend_up = True
            trend_down = False
            take_profit = False

            if not in_long:
                executor.cancel_all_orders()    
                if lowest_low > highest_high * DRAWDOWN_THRESHOLD: leveragenum = 2

                entry = float(df["close"].iloc[-1])
                entry_price_list.append(entry)

                exchange.set_leverage(leverage=int(leveragenum), symbol=SYMBOL)
                raw_qty = ((free_balance * PERCENTAGE_OF_CAPITAL / 100) * leveragenum) / entry
                quantity = float(exchange.amount_to_precision(SYMBOL, raw_qty))

                logging.info(f"Trend Strategy L1 Triggered")
                active_strategy = "TREND"

                executor.enter_long(amount=quantity, leverage=leveragenum)

                # --- SLAVE ENTRY ---
                slaves.enter_long(percentage_of_capital=PERCENTAGE_OF_CAPITAL, leverage=int(leveragenum))
                # -------------------

                executor.place_sl(amount=quantity, price=entry * SLL1)
                executor.place_tp(amount=quantity, price=entry * TPL)

                scalp_long, adaptabletp, tp_is_boosted = False, False, False

            elif in_long and active_strategy == "SCALP":
                if scalp_long and adaptabletp and not tp_is_boosted:
                    logging.info("Trend turned Bullish: Upgrading Scalp TP")
                    pos = exchange.fetch_positions([SYMBOL])[0]
                    amt = abs(float(pos["contracts"]))
                    executor.modify_tp(amount=amt, new_price=entry_price_list[-1] * 1.70)
                    tp_is_boosted = True

        # Trend L2
        if (signal_cur > 0 and failed_l1 and not l2_order and not in_long and not take_profit):
            if active_strategy in [None, "TREND", "SCALP"]:
                trigger_price = entry_price_list[-1] * H1_CLOSE
                if float(bars[-1][4]) >= trigger_price:
                    logging.info(f"Trend Strategy L2 Triggered")
                    exchange.set_leverage(leverage=int(leveragenum), symbol=SYMBOL)
                    raw_qty = ((free_balance * PERCENTAGE_OF_CAPITAL / 100) * leveragenum) / trigger_price
                    quantity = float(exchange.amount_to_precision(SYMBOL, raw_qty))

                    active_strategy = "TREND"
                    executor.enter_long(amount=quantity, leverage=leveragenum)

                    # --- SLAVE ENTRY L2 ---
                    slaves.enter_long(percentage_of_capital=PERCENTAGE_OF_CAPITAL, leverage=int(leveragenum))
                    # ----------------------

                    executor.place_sl(amount=quantity, price=entry_price_list[-1] * H2_SL)
                    l2_order = True

        # Trend Bear Event
        if signal_cur < 0 < signal_prev and not trend_down:
            trend_up, trend_down = False, True
            entry_price_list.append(float(df["close"].iloc[-1]))

            if in_long:
                if active_strategy == "HV":
                    logging.info("Bear Signal Ignored (HV Active)")

                elif active_strategy == "SCALP" and adaptabletp:
                    safe_tp = scalp_entry_list[-1] * 1.25
                    if current_price > safe_tp:
                        executor.exit_long()
                        slaves.exit_long()  # Slave Exit
                    elif tp_is_boosted:
                        pos = exchange.fetch_positions([SYMBOL])[0]
                        amt = abs(float(pos["contracts"]))
                        executor.modify_tp(amount=amt, new_price=safe_tp)
                        tp_is_boosted = False

                elif active_strategy == "TREND" or (active_strategy == "SCALP" and not adaptabletp):
                    executor.exit_long()
                    slaves.exit_long()  # Slave Exit

            if len(entry_price_list) >= 2:
                last, prev = entry_price_list[-1], entry_price_list[-2]
                leveragenum = 2 if last >= prev * PROFIT_THRESHOLD else (
                    max(MIN_LEVERAGE, leveragenum - 3) if last >= prev else min(MAX_LEVERAGE, leveragenum + 1))

            failed_l1, l2_order, take_profit = False, False, False

        # ------------------------------------
        # STRATEGY 2: GENERIC SCALP (Replacing RSI)
        # ------------------------------------
        if is_scalp_territory and not in_long:
            low_price = float(df["low"].iloc[-1])
            scalp_long = True

            # [SANITIZED] Proprietary dynamic ATR risk/reward matrix removed. 
            # Replaced with generic static fallback logic.
            lev, sl, tp, adaptabletp = 3, 0.95, 1.05, False

            exchange.set_leverage(leverage=lev, symbol=SYMBOL)
            raw_qty = ((free_balance * PERCENTAGE_OF_CAPITAL / 101) * lev) / low_price
            quantity = float(exchange.amount_to_precision(SYMBOL, raw_qty))

            logging.info(f"Scalp Entry")
            active_strategy = "SCALP"

            scalp_entry_list.append(low_price)
            entry_price_list.append(low_price)

            executor.enter_long(amount=quantity, leverage=lev)

            # --- SLAVE ENTRY ---
            slaves.enter_long(percentage_of_capital=PERCENTAGE_OF_CAPITAL, leverage=lev)
            # -------------------

            executor.place_sl(quantity, low_price * sl)
            executor.place_tp(quantity, low_price * tp)
            tp_is_boosted = False

            # ------------------------------------
            # STRATEGY 3: GENERIC VOLATILITY (Replacing HV)
            # ------------------------------------
            # Clear leftover SL triggers when a new candle starts
            if is_bar_closed:
                sl_hv_triggered = False

            if volatility_spike and not in_long and hv_traded_bar != bar_time_cur:
                logging.info("HIGH VOLATILITY DETECTED")

                executor.cancel_all_orders()
                exchange.set_leverage(leverage=3, symbol=SYMBOL)

                raw_qty = ((free_balance * PERCENTAGE_OF_CAPITAL / 100) * 3) / hv_last_price
                quantity = float(exchange.amount_to_precision(SYMBOL, raw_qty))

                active_strategy = "HV"
                hv_traded_bar = bar_time_cur  # Lock out L1 for the rest of this candle

                executor.enter_long(quantity, 3)

                # --- SLAVE ENTRY ---
                slaves.enter_long(percentage_of_capital=PERCENTAGE_OF_CAPITAL, leverage=3)
                # -------------------

                executor.place_sl(amount=quantity, price=hv_open * 0.95) # Generic fallback SL
                executor.place_tp(amount=quantity, price=hv_open * 1.10) # Generic fallback TP

                sl_hv_triggered = False

            if active_strategy == "HV" and in_long and is_bar_closed:
                logging.info("BAR CLOSED: HV EXIT")
                executor.cancel_all_orders()
                executor.exit_long()
                slaves.exit_long()
                active_strategy = None

        if not in_position:
            logging.info("Waiting...")
        elif in_long:
            logging.info(f"IN LONG | Mode: {active_strategy}")

    except Exception as e:
        logging.error(f"Loop Error: {e}")
        error_message(f"Loop Error: {e}", StrategyState.VK)
        traceback.print_exc()

    time.sleep(0.5)
