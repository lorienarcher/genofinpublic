import time
import hmac
import hashlib
import json
import base64
import requests
import datetime
import logging
from math import floor
from genofinlib.slack_bot import trade_message, error_message, info_message, StrategyState


# =========================================================
# ==================== BITMEX CLIENT ======================
# =========================================================
class BitmexClient:
    def __init__(self, key, secret, is_testnet=False):
        self.key = key
        self.secret = secret
        self.base_url = "https://testnet.bitmex.com" if is_testnet else "https://www.bitmex.com"
        self.session = requests.Session()

    def _request(self, method, path, data=None):
        url = self.base_url + path
        expires = str(int(time.time() + 10))
        data_str = json.dumps(data) if data else ""

        parsed_url = requests.utils.urlparse(url)
        sig_path = parsed_url.path
        if parsed_url.query:
            sig_path += "?" + parsed_url.query

        message = bytes(method + sig_path + expires + data_str, 'utf-8')
        signature = hmac.new(bytes(self.secret, 'utf-8'), message, hashlib.sha256).hexdigest()

        headers = {
            'api-expires': expires,
            'api-key': self.key,
            'api-signature': signature,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if method == "GET":
            response = self.session.get(url, headers=headers)
        elif method == "POST":
            response = self.session.post(url, headers=headers, data=data_str)

        if not response.ok:
            raise Exception(f"BitMEX API Error ({response.status_code}): {response.text}")
        return response.json()

    def get_balance(self):
        res = self._request("GET", "/api/v1/user/margin?currency=all")
        if isinstance(res, list):
            for item in res:
                if item.get('currency') == 'USDt':
                    return float(item.get('availableMargin', 0)) / 1000000.0
        return 0.0

    def get_ticker_and_contract_size(self, symbol):
        res = self._request("GET", f"/api/v1/instrument?symbol={symbol}&count=1&reverse=true")
        if res and len(res) > 0:
            data = res[0]
            last_price = float(data.get('lastPrice', 0))
            lot_size = float(data.get('lotSize', 1.0))

            pos_mult = data.get('underlyingToPositionMultiplier')
            if pos_mult is not None and float(pos_mult) > 0:
                contract_size = 1.0 / float(pos_mult)
            else:
                mult = data.get('multiplier', 1000)
                contract_size = float(mult) / 1000000.0

            return last_price, contract_size, lot_size
        raise Exception(f"Ticker for {symbol} not found")

    def set_leverage(self, symbol, leverage):
        try:
            self._request("POST", "/api/v1/position/leverage", {"symbol": symbol, "leverage": str(leverage)})
        except:
            pass

    def create_market_order(self, symbol, side, orderQty, reduceOnly=False):
        data = {"symbol": symbol, "side": side, "orderQty": int(orderQty), "ordType": "Market"}
        if reduceOnly:
            data["execInst"] = "ReduceOnly"
        return self._request("POST", "/api/v1/order", data)

    def get_positions(self, symbol):
        import urllib.parse
        filter_json = json.dumps({'symbol': symbol}, separators=(',', ':'))
        encoded_filter = urllib.parse.quote(filter_json)
        return self._request("GET", f"/api/v1/position?filter={encoded_filter}")


# =========================================================
# ====================== OKX CLIENT =======================
# =========================================================
class OkxClient:
    def __init__(self, key, secret, passphrase, is_testnet=False):
        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.base_url = "https://www.okx.com"
        self.is_testnet = is_testnet
        self.session = requests.Session()

    def _get_timestamp(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        return now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _sign(self, timestamp, method, requestPath, body):
        message = str(timestamp) + str(method) + str(requestPath) + str(body)
        mac = hmac.new(bytes(self.secret, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        return base64.b64encode(mac.digest()).decode('utf-8')

    def _request(self, method, requestPath, data=None):
        url = self.base_url + requestPath
        body = json.dumps(data) if data else ""
        timestamp = self._get_timestamp()
        sign = self._sign(timestamp, method, requestPath, body)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase
        }
        if self.is_testnet:
            headers["x-simulated-trading"] = "1"

        if method == "GET":
            res = self.session.get(url, headers=headers)
        elif method == "POST":
            res = self.session.post(url, headers=headers, data=body)

        json_data = res.json()
        if str(json_data.get("code", "0")) != "0":
            raise Exception(f"OKX API Error: {res.text}")
        return json_data

    def set_position_mode(self, is_hedge=False):
        mode = "long_short_mode" if is_hedge else "net_mode"
        try:
            self._request("POST", "/api/v5/account/set-position-mode", {"posMode": mode})
        except:
            pass

    def get_balance(self):
        res = self._request("GET", "/api/v5/account/balance?ccy=USDT")
        data = res.get("data", [])
        if len(data) > 0:
            details = data[0].get("details", [])
            for ccy in details:
                if ccy.get("ccy") == "USDT":
                    return float(ccy.get("availEq", 0))
        return 0.0

    def get_ticker_and_contract(self, instId):
        tick_res = self._request("GET", f"/api/v5/market/ticker?instId={instId}")
        last_price = float(tick_res["data"][0]["last"])
        inst_res = self._request("GET", f"/api/v5/public/instruments?instType=SWAP&instId={instId}")
        contract_size = float(inst_res["data"][0]["ctVal"])
        min_amount = float(inst_res["data"][0]["minSz"])
        lot_size = float(inst_res["data"][0]["lotSz"])
        return last_price, contract_size, min_amount, lot_size

    def set_leverage(self, instId, leverage):
        try:
            self._request("POST", "/api/v5/account/set-leverage", {
                "instId": instId, "lever": str(leverage), "mgnMode": "cross"
            })
        except:
            pass

    def create_market_order(self, instId, side, sz, posSide=None, reduceOnly=False):
        data = {"instId": instId, "tdMode": "cross", "side": side, "ordType": "market", "sz": str(sz)}
        if posSide: data["posSide"] = posSide
        if reduceOnly: data["reduceOnly"] = True
        return self._request("POST", "/api/v5/trade/order", data)

    def get_positions(self, instId):
        res = self._request("GET", f"/api/v5/account/positions?instId={instId}")
        return res.get("data", [])


# =========================================================
# ==================== SLAVE MANAGER ======================
# =========================================================
class SlaveManager:
    def __init__(self, config, is_testnet=False):
        self.okx = None
        self.bitmex = None
        self.symbol_base = config.symbol_name.upper()

        bm_key = config.bitmex_test_key if is_testnet else config.bitmex_copy_key
        bm_secret = config.bitmex_test_secret if is_testnet else config.bitmex_copy_secret
        okx_key = config.okx_test_key if is_testnet else config.okx_copy_key
        okx_secret = config.okx_test_secret if is_testnet else config.okx_copy_secret
        okx_pass = config.okx_test_pass if is_testnet else config.okx_copy_pass

        if bm_key and bm_secret:
            self.bitmex = BitmexClient(bm_key, bm_secret, is_testnet)
            info_message(f"Slave Connected: BITMEX ({'TESTNET' if is_testnet else 'MAINNET'})", StrategyState.VK)
            logging.info(f"Slave Connected: BITMEX ({'TESTNET' if is_testnet else 'MAINNET'})")
        if okx_key and okx_secret:
            self.okx = OkxClient(okx_key, okx_secret, okx_pass, is_testnet)
            info_message(f"Slave Connected: OKX ({'TESTNET' if is_testnet else 'MAINNET'})", StrategyState.VK)
            logging.info(f"Slave Connected: OKX ({'TESTNET' if is_testnet else 'MAINNET'})")
            self.okx.set_position_mode(False)

    def enter_long(self, percentage_of_capital, leverage):
        self.open_long_bitmex(percentage_of_capital, leverage)
        self.open_long_okx(percentage_of_capital, leverage)

    def exit_long(self):
        self.close_long_bitmex()
        self.close_long_okx()

    def get_bitmex_symbol(self):
        base = "XBT" if self.symbol_base == "BTC" else self.symbol_base
        return f"{base}USDT"

    def open_long_bitmex(self, percentage, leverage):
        if not self.bitmex: return
        try:
            symbol = self.get_bitmex_symbol()
            usdt_free = self.bitmex.get_balance()
            if usdt_free <= 5: return

            price, contract_size, lot_size = self.bitmex.get_ticker_and_contract_size(symbol)
            # [SANITIZED] Proprietary notional and margin buffer multipliers removed
            raw_contracts = (usdt_free * (percentage / 100) * leverage) / (price * contract_size)
            contracts = int(floor(raw_contracts / lot_size) * lot_size)

            if contracts > 0:
                self.bitmex.create_market_order(symbol, "Buy", contracts)
                trade_message(f"BITMEX Long Opened | Qty: {contracts}", StrategyState.VK)
        except Exception as e:
            error_message(f"BITMEX Entry Failed: {e}", StrategyState.VK)

    def close_long_bitmex(self):
        if not self.bitmex: return
        try:
            symbol = self.get_bitmex_symbol()
            positions = self.bitmex.get_positions(symbol)
            for pos in positions:
                amt = float(pos.get('currentQty', 0))
                if amt > 0:
                    self.bitmex.create_market_order(symbol, "Sell", amt, reduceOnly=True)
                    trade_message(f"BITMEX Long Closed", StrategyState.VK)
        except:
            pass

    def get_okx_symbol(self):
        return f"{self.symbol_base}-USDT-SWAP"

    def open_long_okx(self, percentage, leverage):
        if not self.okx: return
        try:
            import math
            symbol = self.get_okx_symbol()
            usdt_free = self.okx.get_balance()
            if usdt_free <= 5: return

            price, contract_size, min_amount, lot_size = self.okx.get_ticker_and_contract(symbol)
            # [SANITIZED] Proprietary margin buffer removed
            raw_contracts = (usdt_free * (percentage / 100) * leverage) / (price * contract_size)
            contracts = math.floor(raw_contracts / lot_size) * lot_size

            # Precision formatting
            if contracts.is_integer():
                contracts = int(contracts)
            else:
                decimals = max(0, int(round(-math.log(lot_size, 10), 0)))
                contracts = round(contracts, decimals)

            if contracts >= min_amount:
                self.okx.create_market_order(symbol, "buy", contracts)
                trade_message(f"OKX Long Opened | Qty: {contracts}", StrategyState.VK)
        except Exception as e:
            error_message(f"OKX Entry Failed: {e}", StrategyState.VK)

    def close_long_okx(self):
        if not self.okx: return
        try:
            symbol = self.get_okx_symbol()
            positions = self.okx.get_positions(symbol)
            for pos in positions:
                contracts = float(pos.get('pos', 0))
                if contracts > 0:
                    self.okx.create_market_order(symbol, "sell", contracts, reduceOnly=True)
                    trade_message(f"OKX Long Closed", StrategyState.VK)
        except:
            pass