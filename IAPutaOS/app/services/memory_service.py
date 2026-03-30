import sqlite3

DB_PATH = "iaputa_os_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabla para contexto key-value (mantenemos la antigua por compatibilidad si es necesario)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS context_memory (
            key TEXT PRIMARY KEY, 
            value TEXT, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Nueva tabla para el historial del chat
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role: str, content: str):
    if not content:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (role, content) VALUES (?, ?)",
        (role, content)
    )
    conn.commit()
    conn.close()

def get_recent_history(limit: int = 8) -> list:
    """Obtiene los últimos N mensajes para pasárselos al LLM como memoria contextual."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_history ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    # Invertir para que estén en orden cronológico ascendente (los más antiguos primero)
    for row in reversed(rows):
        history.append({"role": row[0], "content": row[1]})
    return history

def clear_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()

# Inicializamos las tablas al importar el módulo
init_db()
