import threading
import requests
from app.config import get_required_environ
 
TELEGRAM_BOT_TOKEN = get_required_environ("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
 
 
def get_updates(offset=None):
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        return response.json().get("result", [])
    except Exception:
        return []
 
 
def send_message(chat_id, text):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception:
        pass
 
 
def handle_updates(updates):
    from app.db.users import UserResource, NOTIFICATION_PREFS
    user_res = UserResource()
    for update in updates:
        message = update.get("message")
        if not message:
            continue
        chat_id = str(message["chat"]["id"])
        phone = message.get("text", "").strip()
        # Look up user by the phone number they sent
        user = user_res.get_user_by_phone(phone)
        if user is None:
            send_message(chat_id, "Phone number not found. Please send your phone number in the format you registered with (eg. +97150000000).")
            continue
        # Only link if user has telegram in their preferences
        prefs = user.get(NOTIFICATION_PREFS, [])
        if "telegram" not in prefs:
            send_message(chat_id, "You have not enabled Telegram notifications. Update your preferences first.")
            continue
        user_res.save_telegram_chat_id(user["_id"], chat_id)
        send_message(chat_id, "You are now set up to receive Telegram notifications!")
 
 
def poll():
    offset = None
    while True:
        updates = get_updates(offset)
        if updates:
            handle_updates(updates)
            offset = updates[-1]["update_id"] + 1
 
 
def start_polling():
    thread = threading.Thread(target=poll, daemon=True)
    thread.start()