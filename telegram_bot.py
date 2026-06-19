"""
Telegram Bot API দিয়ে মেসেজ পাঠানো ও chat_id খুঁজে বের করার হেল্পার ফাংশন।
"""

import requests


def send_message(token: str, chat_id: str, text: str):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        resp = requests.post(url, json=payload, timeout=15)
        if not resp.ok:
            print(f"[telegram_bot] Send failed: {resp.text}")
        return resp.ok
    except Exception as e:
        print(f"[telegram_bot] Send error: {e}")
        return False


def get_updates(token: str):
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        resp = requests.get(url, timeout=15)
        return resp.json()
    except Exception as e:
        print(f"[telegram_bot] getUpdates error: {e}")
        return None
