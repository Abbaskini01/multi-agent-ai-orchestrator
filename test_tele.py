import os
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

def send_telegram_message(message: str):
    """Sends a direct text alert using built-in Python tools."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("[Error] Missing Telegram environment credentials in .env file.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("-> Success! Telegram notification fired cleanly to your device.")
                return True
    except Exception as e:
        print(f"-> Failed to send Telegram alert: {e}")
        return False

if __name__ == "__main__":
    print("Testing standalone Telegram notification connection...")
    send_telegram_message("🤖 *Orchestrator Alert:* Standalone link test successful! Connected to your local workspace.")