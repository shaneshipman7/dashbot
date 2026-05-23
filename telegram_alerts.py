# telegram_alerts.py
import requests
from datetime import datetime

TELEGRAM_TOKEN = "8715090537:AAEjRVKQznU_uYcbztSdIUayrEgAByNh-iY"
TELEGRAM_CHAT_ID = "8766002126"

def send_alert(message: str, parse_mode: str = "Markdown"):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Alert sent at {datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            print(f"❌ Telegram Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")
        return False