import requests
from app.config import get_required_environ

TELEGRAM_BOT_TOKEN = get_required_environ("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def send_reminder_telegram(chat_id: str, recipient_name: str, class_name: str, start_time: str, location: str) -> bool:
    """
    Send a reminder message via Telegram Bot API
    Returns True on success, False on failure
    """
    text = (
        f"Hi {recipient_name},\n\n"
        f"This is a reminder that you are registered for {class_name}.\n"
        f"Start time: {start_time}\n"
        f"Location: {location}\n\n"
        f"See you there!"
    )
    message_data = {
        "chat_id": chat_id,
        "text": text,
    }
    try:
        response = requests.post(TELEGRAM_API_URL, json=message_data, timeout=10)
        return response.status_code == 200
    except Exception:
        return False