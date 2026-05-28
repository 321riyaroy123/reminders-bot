import os
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Send a Telegram message to TELEGRAM_CHAT_ID using TELEGRAM_BOT_TOKEN.
    Returns True on success, False on failure.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are required."
        )

    url = TELEGRAM_API.format(token=token, method="sendMessage")
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"Telegram message sent: {text[:60]}...")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def test_connection() -> bool:
    """Verify bot token works by calling getMe."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    try:
        url = TELEGRAM_API.format(token=token, method="getMe")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        bot_info = resp.json().get("result", {})
        logger.info(f"Connected to Telegram bot: @{bot_info.get('username')}")
        return True
    except Exception as e:
        logger.error(f"Telegram connection test failed: {e}")
        return False
