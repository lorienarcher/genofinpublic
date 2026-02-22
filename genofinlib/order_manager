import time
import logging
import requests
import hmac
import hashlib
import urllib.parse
import math
from .slack_bot import StrategyState, trade_message, error_message


class OrderManager:
    def __init__(self, ws_api, symbol, api_key, api_secret, is_testnet=False):
        self.ws_api = ws_api
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_testnet = is_testnet
        self.base_url = "https://testnet.binancefuture.com" if is_testnet else "https://fapi.binance.com"
        self.active_tp_id = None

        self.markets = {}
        self.session = requests.Session()
        self.session.headers.update({'X-MBX-APIKEY': self.api_key})

    def _request(self, method, endpoint, params=None, signed=False):
        params = params or {}
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 10000
            query_string = urllib.parse.urlencode(params)
            signature = hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'),
                                 hashlib.sha256).hexdigest()
            url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        else:
            query_string = urllib.parse.urlencode(params)
            url = f"{self.base_url}{endpoint}?{query_string}" if query_string else f"{self.base_url}{endpoint}"

        res = self.session.request(method, url)
        if not res.ok:
            raise Exception(f"Binance API Error ({res.status_code}): {res.text}")
        return res.json()

    # ==========================================
    # DATA & MARKET METHODS (Replacing CCXT)
    # ==========================================
    def load_markets(self):
        info = self._request("GET", "/fapi/v1/exchangeInfo")
        for symbol_data in info['symbols']:
            filters = {f['filterType']: f for f in symbol_data['filters']}
            self.markets[symbol_data['symbol']] = {
                'stepSize': float(filters.get('LOT_SIZE', {}).get('stepSize', 0.001)),
                'tickSize': float(filters.get('PRICE_FILTER', {}).get('tickSize', 0.001))
            }
        return self.markets

    def fetch_ohlcv(self, symbol, timeframe, limit=1500):
        binance_symbol = symbol.replace("/", "")
        klines = self._request("GET", "/fapi/v1/klines",
                               {'symbol': binance_symbol, 'interval': timeframe, 'limit': limit})
        return [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in klines]

    def fetch_balance(self):
        account = self._request("GET", "/fapi/v2/account", signed=True)
        return {'info': account}

    def fetch_positions(self, symbols=None):
        raw_positions = self._request("GET", "/fapi/v2/positionRisk", signed=True)
        if symbols:
            binance_symbols = [s.replace("/", "") for s in symbols]
            raw_positions = [p for p in raw_positions if p['symbol'] in binance_symbols]
        return [{'symbol': p['symbol'], 'contracts': float(p['positionAmt']), 'positionAmt': p['positionAmt']} for p in
                raw_positions]

    def set_leverage(self, leverage, symbol):
        binance_symbol = symbol.replace("/", "")
        return self._request("POST", "/fapi/v1/leverage", {'symbol': binance_symbol, 'leverage': leverage}, signed=True)

    def amount_to_precision(self, symbol, amount):
        binance_symbol = symbol.replace("/", "")
        step_size = self.markets.get(binance_symbol, {}).get('stepSize', 0.001)
        precision = int(round(-math.log(step_size, 10), 0))
        return f"{amount:.{precision}f}"

    def price_to_precision(self, symbol, price):
        binance_symbol = symbol.replace("/", "")
        tick_size = self.markets.get(binance_symbol, {}).get('tickSize', 0.001)
        precision = int(round(-math.log(tick_size, 10), 0))
        return f"{price:.{precision}f}"

    def enable_demo_trading(self, enable):
        pass  # Handled inherently by the is_testnet flag in __init__

    # ==========================================
    # ORDER MANAGEMENT METHODS
    # ==========================================
    def cancel_all_orders(self):
        # 1. Cancel Standard via REST (Replacing CCXT cancel)
        try:
            binance_symbol = self.symbol.replace("/", "")
            self._request("DELETE", "/fapi/v1/allOpenOrders", {'symbol': binance_symbol}, signed=True)
        except:
            pass

        # 2. Cancel Algo via REST
        try:
            self._request("DELETE", "/fapi/v1/algoOpenOrders", {'symbol': self.symbol.replace('/', '')}, signed=True)
        except Exception as e:
            logging.error(f"Algo Cancel Error: {e}")
            trade_message(f"Algo Cancel Error: {e}", StrategyState.VK)

        logging.info("All Orders Cancelled")
        trade_message("All Orders Cancelled", StrategyState.VK)

    def cancel_algo_order(self, client_algo_id):
        self.ws_api.send_request("algoOrder.cancel", {
            "symbol": self.symbol.replace('/', ''),
            "clientAlgoId": client_algo_id
        })

    def enter_long(self, amount, leverage):
        self.ws_api.send_request("order.place", {
            "symbol": self.symbol.replace('/', ''), "side": "BUY", "type": "MARKET", "quantity": amount
        })
        log_msg = f"Long Entry | Qty: {amount} | Lev: {leverage}"
        logging.info(log_msg)
        trade_message(log_msg, StrategyState.VK)

    def exit_long(self):
        try:
            pos = self.fetch_positions([self.symbol])[0]
            amt = abs(float(pos["contracts"]))
            if amt > 0:
                self.ws_api.send_request("order.place", {
                    "symbol": self.symbol.replace('/', ''), "side": "SELL", "type": "MARKET", "quantity": amt,
                    "reduceOnly": True
                })
                log_msg = f"Long Exit | Closed Qty: {amt}"
                logging.info(log_msg)
                trade_message(log_msg, StrategyState.VK)
        except Exception as e:
            logging.error(f"Exit Error: {e}")
            error_message(f"Long Exit Error: {e}", StrategyState.VK)

    def place_sl(self, amount, price):
        ts = str(int(time.time()))
        final_price = self.price_to_precision(self.symbol, price)

        self.ws_api.send_request("algoOrder.place", {
            "algoType": "CONDITIONAL", "symbol": self.symbol.replace('/', ''), "side": "SELL", "type": "STOP_MARKET",
            "quantity": amount, "triggerPrice": final_price, "reduceOnly": True, "workingType": "MARK_PRICE",
            "priceProtect": True, "clientAlgoId": f"SL_L1_{ts}"
        })
        logging.info(f"SL Sent| Qty: {amount} | Price: {final_price}")
        trade_message(f"SL Sent | Qty: {amount} | Prc: {final_price}", StrategyState.VK)

    def place_tp(self, amount, price):
        ts = str(int(time.time()))
        cid = f"TP_{ts}"
        self.active_tp_id = cid

        final_price = self.price_to_precision(self.symbol, price)

        self.ws_api.send_request("algoOrder.place", {
            "algoType": "CONDITIONAL", "symbol": self.symbol.replace('/', ''), "side": "SELL",
            "type": "TAKE_PROFIT_MARKET",
            "quantity": amount, "triggerPrice": final_price, "reduceOnly": True, "workingType": "CONTRACT_PRICE",
            "clientAlgoId": cid
        })
        logging.info(f"TP Sent| Qty: {amount} | Price: {final_price}")
        trade_message(f"TP Sent | Qty: {amount} | Prc: {final_price}", StrategyState.VK)

    def modify_tp(self, amount, new_price):
        if self.active_tp_id:
            self.cancel_algo_order(self.active_tp_id)
            time.sleep(0.5)
        self.place_tp(amount, new_price)
        logging.info(f"TP Modified | Qty: {amount} | Price: {new_price}")
        trade_message(f"TP Modified to {new_price}", StrategyState.VK)
