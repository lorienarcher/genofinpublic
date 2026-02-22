import json
import logging
import time
import hmac
import hashlib
import websocket
import threading
from urllib.parse import urlencode
from .slack_bot import StrategyState, error_message, info_message

class WebSocketApiManager:
    def __init__(self, api_key, api_secret, ws_url, is_testnet):
        self.ws = None
        self.is_connected = False
        self.id_counter = 1
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = ws_url
        self.is_testnet = is_testnet

    def on_open(self, ws):
        net_type = 'TESTNET' if self.is_testnet else 'MAINNET'
        logging.info(f"Trading Websocket Connected ({net_type})")
        info_message(f"Trading Websocket Connected ({net_type})", StrategyState.VK)
        self.is_connected = True

    def on_close(self, ws, close_status_code, close_msg):
        logging.warning(f"Trading WS Disconnected: {close_msg}")
        info_message(f"Trading Websocket Disconnected {close_msg}", StrategyState.VK)
        self.is_connected = False

    def on_error(self, ws, error):
        logging.error(f"Trading WS Error: {error}")
        error_message(f"Trading WS Error: {error}", StrategyState.VK)

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if 'error' in data:
                err = data['error']
                if err.get('code') == -2011: return
                logging.error(f"WS API Error: {err}")
                error_message(f"WS API Error: {err}", StrategyState.VK)
            elif 'result' in data:
                res = data['result']
                if isinstance(res, dict) and 'orderId' in res:
                    logging.info(f"WS Order Success | ID: {res['orderId']}")
                elif isinstance(res, dict) and 'algoId' in res:
                    logging.info(f"WS Algo Success | ID: {res['algoId']}")
        except Exception as e:
            logging.error(f"WS Parse Error: {e}")
            error_message(f"WS Parse Error: {e}", StrategyState.VK)

    def connect(self):
        def run():
            while True:
                try:
                    self.ws = websocket.WebSocketApp(
                        self.ws_url, on_open=self.on_open, on_close=self.on_close,
                        on_error=self.on_error, on_message=self.on_message)
                    self.ws.run_forever()
                except Exception as e:
                    logging.error(f"Trading WS Reconnect Error: {e}")
                    error_message(f"Trading WS Reconnect Error: {e}", StrategyState.VK)
                    time.sleep(5)
        threading.Thread(target=run, daemon=True).start()
        time.sleep(2)

    def send_request(self, method, params=None):
        if not self.is_connected: return
        if params is None: params = {}

        clean_params = {k: ('true' if v is True else 'false' if v is False else v) for k, v in params.items()}
        clean_params['apiKey'] = self.api_key
        clean_params['timestamp'] = int(time.time() * 1000)

        query_string = urlencode(sorted(clean_params.items()))
        signature = hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        clean_params['signature'] = signature

        req_id = f"req_{self.id_counter}"
        self.id_counter += 1

        try:
            self.ws.send(json.dumps({"id": req_id, "method": method, "params": clean_params}))
            logging.info(f"WS SENT: {method} | ID: {req_id}")
        except Exception as e:
            logging.error(f"WS Send Failed: {e}")
            error_message(f"WS Send Failed: {e}", StrategyState.VK)
