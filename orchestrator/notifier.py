import os
import requests
from orchestrator.state import OrchestratorState


def notifier_node(state: OrchestratorState) -> dict:
    """
    Notifier Node:
    Sends Telegram notification upon build completion.
    """
    print("\n[Node Activating] ---> Telegram Notifier Node")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("-> Notice: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env. Skipping Telegram ping.")
        return {}
        
    proj_name = state.get("project_name", "GeneratedApp")
    arch = state.get("architecture_pattern", "N/A")
    tasks_count = len(state.get("tasks", []))
    retries = state.get("retry_count", 0)
    
    msg = (
        f"🚀 *Build Completed Successfully!*\n\n"
        f"📦 *Project:* `{proj_name}`\n"
        f"🏛️ *Architecture:* `{arch}`\n"
        f"📄 *Files Generated:* `{tasks_count}`\n"
        f"🛠️ *Self-Repair Iterations:* `{retries}`\n\n"
        f"All quality gates (Syntax, Docker Runtime, Dynamic Unittests) passed!"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown"
    }
    
    try:
        print("-> Pinging outbound mobile notification stream...")
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            print("-> Telegram notification sent successfully!")
        else:
            print(f"-> Warning: Telegram API returned status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"-> Warning: Failed to send Telegram notification: {e}")

    return {}