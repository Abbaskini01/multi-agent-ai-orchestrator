"""
Neural Glass AI Orchestrator — Persistent Memory & Context Engine
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path("workspace_sandbox/orchestrator_memory.db")


def init_memory_db():
    """Initializes the persistent memory SQLite schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Session / Prompt Memory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT NOT NULL,
            parsed_intent TEXT,
            files_generated TEXT
        )
    """)
    
    # Repair Pattern Memory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repair_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_name TEXT NOT NULL,
            error_category TEXT NOT NULL,
            error_details TEXT NOT NULL,
            solution_summary TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def save_session_memory(prompt: str, intent: str, files: Dict[str, str]):
    """Records a completed execution run into persistent memory."""
    init_memory_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO session_memory (prompt, parsed_intent, files_generated) VALUES (?, ?, ?)",
        (prompt, intent, json.dumps(list(files.keys())))
    )
    conn.commit()
    conn.close()


def save_repair_memory(file_name: str, category: str, details: str, solution: str = ""):
    """Stores successful repair patterns for future contextual retrieval."""
    init_memory_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO repair_memory (file_name, error_category, error_details, solution_summary) VALUES (?, ?, ?, ?)",
        (file_name, category, details[:500], solution[:500])
    )
    conn.commit()
    conn.close()


def get_relevant_repairs(category: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Retrieves past repair patterns matching a given error category."""
    init_memory_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT file_name, error_details, solution_summary FROM repair_memory WHERE error_category = ? ORDER BY id DESC LIMIT ?",
        (category, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"file_name": r[0], "error_details": r[1], "solution_summary": r[2]}
        for r in rows
    ]


def get_memory_history() -> Dict[str, Any]:
    """Returns recent session and repair history for API reporting."""
    init_memory_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, timestamp, prompt, parsed_intent FROM session_memory ORDER BY id DESC LIMIT 10")
    sessions = cursor.fetchall()
    
    cursor.execute("SELECT id, timestamp, file_name, error_category FROM repair_memory ORDER BY id DESC LIMIT 10")
    repairs = cursor.fetchall()
    
    conn.close()
    return {
        "sessions": [{"id": s[0], "time": s[1], "prompt": s[2], "intent": s[3]} for s in sessions],
        "repairs": [{"id": r[0], "time": r[1], "file": r[2], "category": r[3]} for r in repairs]
    }