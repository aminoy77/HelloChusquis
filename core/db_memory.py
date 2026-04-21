import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


MEMORY_DB_PATH = Path.home() / ".hellochusquis/memory.db"


def init_db():
    """Inicializa la base de datos SQLite y crea tablas necesarias."""
    MEMORY_DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def save_session(messages: List[Dict[str, Any]]) -> None:
    """Guarda una sesión completa en la base de datos."""
    if not messages:
        return
    
    init_db()
    timestamp = datetime.now().isoformat()
    data = str(messages)  # Podría serializarse mejor en producción
    
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (timestamp, data) VALUES (?, ?)", (timestamp, data))
    conn.commit()
    conn.close()


def load_last_session() -> List[Dict[str, Any]]:
    """Carga la última sesión guardada."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM sessions ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return eval(row[0])  # Mejor usar json.loads en producción
    return []


def save_summary(summary: str) -> None:
    """Guarda o actualiza el resumen de sesiones pasadas."""
    init_db()
    updated_at = datetime.now().isoformat()
    
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM summaries")
    cursor.execute("INSERT INTO summaries (content, updated_at) VALUES (?, ?)", (summary, updated_at))
    conn.commit()
    conn.close()


def load_summary() -> str:
    """Carga el último resumen guardado."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM summaries ORDER BY updated_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return ""
