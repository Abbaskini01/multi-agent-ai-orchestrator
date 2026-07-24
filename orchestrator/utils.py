import os
import re
import urllib.request
import urllib.parse

def clean_extracted_code(output_text: str) -> str:
    """Isolates raw Python code from markdown wraps and fixes over-escaped newlines."""
    python_block_match = re.search(r"```python\s*(.*?)\s*```", output_text, re.DOTALL)
    if python_block_match:
        output_text = python_block_match.group(1)
    else:
        generic_block_match = re.search(r"```\s*(.*?)\s*```", output_text, re.DOTALL)
        if generic_block_match:
            output_text = generic_block_match.group(1)
        else:
            output_text = output_text.strip()
            
    # Fix double-escaped literal \n sequences if code was over-escaped in JSON
    if "\\n" in output_text and "\n" not in output_text:
        output_text = output_text.replace("\\n", "\n")
        
    return output_text


def send_telegram_message(message: str) -> bool:
    """Sends a direct text alert to Telegram with plain-text fallback."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("[Error] Missing Telegram environment credentials in .env file.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload_markdown = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    data_markdown = urllib.parse.urlencode(payload_markdown).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data_markdown, method="POST")
        with urllib.request.urlopen(req) as response:
            return response.status == 200
    except Exception:
        clean_text = message.replace("*", "").replace("`", "").replace("_", "")
        payload_plain = {"chat_id": chat_id, "text": clean_text}
        data_plain = urllib.parse.urlencode(payload_plain).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data_plain, method="POST")
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as fallback_err:
            print(f"-> Failed to send Telegram alert: {fallback_err}")
            return False