"""
Neural Glass AI Orchestrator — Team Collaboration Engine
"""

import time
from typing import Dict, List, Any
from core.logger import log_event

# In-memory storage for presence and inline comment threads
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {
    "dev_alice": {
        "user": "Alice",
        "active_file": "server.py",
        "last_seen": time.time(),
        "status": "active"
    },
    "dev_bob": {
        "user": "Bob",
        "active_file": "core/security.py",
        "last_seen": time.time() - 120,
        "status": "idle"
    }
}

COMMENT_THREADS: List[Dict[str, Any]] = []


def get_team_presence() -> Dict[str, Any]:
    """Returns active developer sessions, active files, and workspace locks."""
    return {
        "active_users_count": len(ACTIVE_SESSIONS),
        "sessions": list(ACTIVE_SESSIONS.values()),
        "total_comments": len(COMMENT_THREADS)
    }


def add_inline_comment(author: str, file_path: str, line: int, comment: str) -> Dict[str, Any]:
    """Attaches a peer-review or developer discussion comment thread to a file location."""
    comment_entry = {
        "id": f"comment_{len(COMMENT_THREADS) + 1}",
        "author": author,
        "file": file_path,
        "line": line,
        "comment": comment,
        "timestamp": time.time()
    }
    COMMENT_THREADS.append(comment_entry)
    log_event("team_comment_added", author=author, file=file_path, line=line)
    
    return {
        "status": "success",
        "comment_id": comment_entry["id"],
        "total_threads": len(COMMENT_THREADS)
    }