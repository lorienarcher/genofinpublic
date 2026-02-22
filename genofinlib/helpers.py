import requests
import time
import logging
from .slack_bot import StrategyState, error_message

def get_listen_key(api_key, base_url):
    try:
        headers = {"X-MBX-APIKEY": api_key}
        return requests.post(f"{base_url}/fapi/v1/listenKey", headers=headers).json()["listenKey"]
    except Exception as e:
        logging.error(f"ListenKey Error: {e}")
        error_message(f"ListenKey Error: {e}", StrategyState.VK)
        return None

def keep_alive_listen_key(api_key, base_url):
    while True:
        time.sleep(1800)  # Ping every 30 minutes to keep the socket alive
        try:
            requests.put(f"{base_url}/fapi/v1/listenKey", headers={"X-MBX-APIKEY": api_key})
            logging.info("ListenKey Refreshed")
        except:
            pass
