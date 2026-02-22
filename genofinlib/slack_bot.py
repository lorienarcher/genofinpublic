import logging
import threading
from enum import Enum
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import trader.config as config
import trader.config_test as config_test
from trader.valkyrie_trader import IS_TESTNET

if IS_TESTNET:
    cfg = config_test
else:
    cfg = config

SLACK_TOKEN = cfg.slack_token
SLACK_CHANNEL = cfg.slack_channel


class StrategyState(Enum):
    VK = "Valkyrie"
    ST = "Trend Strategy"       # [SANITIZED] Proprietary strategy name masked
    HV = "Volatility Strategy"  # [SANITIZED] Proprietary strategy name masked
    RSI = "Scalp Strategy"      # [SANITIZED] Proprietary strategy name masked


class SlackNotifier:
    def __init__(self, token, channel):
        self.client = None
        self.channel = channel
        self.enabled = False

        if token:
            try:
                self.client = WebClient(token=token)
                self.enabled = True
            except Exception as e:
                logging.error(f"Failed to initialize Slack Client: {e}")
        else:
            logging.warning("Slack Token is empty. Notifications disabled.")

    def _send_thread(self, text, color, title):
        """Executed in a background thread to prevent blocking the trading loop"""
        if not self.enabled or not self.client:
            return

        try:
            # Create a rich attachment with color
            attachment = {
                "color": color,
                "fallback": f"{title}: {text}", # This shows on mobile notifications
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{title}*\n{text}"
                        }
                    }
                ]
            }

            self.client.chat_postMessage(
                channel=self.channel,
                attachments=[attachment],
                text=""  # FIX: Set to empty to prevent double message in chat
            )
        except SlackApiError as e:
            logging.error(f"Slack API Error: {e.response['error']}")
        except Exception as e:
            logging.error(f"Slack Send Error: {e}")

    def send(self, message, strategy: StrategyState, msg_type="INFO", color="#3498db"):
        """Spawns a thread to send the message"""
        title = f"[{msg_type}] - {strategy.value}"
        # Daemon thread ensures it doesn't block program exit
        threading.Thread(target=self._send_thread, args=(message, color, title), daemon=True).start()


# Initialize the Notifier ONCE
notifier = SlackNotifier(SLACK_TOKEN, SLACK_CHANNEL)


# ==========================================
# WRAPPER FUNCTIONS (API Compatible)
# ==========================================

def info_message(message: str, strategy: StrategyState):
    """
    Sends an informational message.
    Color: Blue
    """
    notifier.send(message, strategy, msg_type="INFO", color="#3498db")  


def trade_message(message: str, strategy: StrategyState):
    """
    Sends a trade execution message.
    Color: Green
    """
    notifier.send(message, strategy, msg_type="TRADE", color="#2ecc71")  


def error_message(message: str, strategy: StrategyState):
    """
    Sends an error message.
    Color: Red
    """
    notifier.send(message, strategy, msg_type="ERROR", color="#e74c3c")
