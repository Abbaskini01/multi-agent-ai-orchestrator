from orchestrator.state import OrchestratorState
from orchestrator.utils import send_telegram_message

def notification_node(state: OrchestratorState) -> dict:
    """Notification Agent: Sends final status report via Telegram."""
    print("\n[Node Activating] ---> Notification Node")
    
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)
    tasks = state.get("tasks", [])
    
    if not error:
        file_list_str = "\n".join([f"• `{t['filename']}`" for t in tasks])
        alert_text = (
            f"✅ *Project Exported & Verified!*\n\n"
            f"*Requirement:* {state['user_requirement']}\n\n"
            f"*Generated Files:*\n{file_list_str}\n"
            f"• `README.md`\n• `.gitignore`\n\n"
            f"*Git Repository:* Initialized & Committed\n"
            f"*Total Retries Required:* {retries}"
        )
    else:
        alert_text = (
            f"❌ *Orchestration Aborted!*\n\n"
            f"*Requirement:* {state['user_requirement']}\n\n"
            f"*Last Logged Exception:*\n```\n{error}\n```"
        )
        
    print("-> Pinging outbound mobile notification stream...")
    send_telegram_message(alert_text)
    return {}