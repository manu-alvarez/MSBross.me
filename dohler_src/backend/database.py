"""
SQLite Database Module for DOHLER Task Manager
Provides async database operations using aiosqlite
"""
import aiosqlite
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.db")

# SQL to create tasks table
CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    deadline TEXT,
    priority TEXT DEFAULT 'Medium',
    dependencies TEXT DEFAULT '[]',
    recurring INTEGER DEFAULT 0,
    recurring_interval TEXT DEFAULT 'Daily',
    created_at TEXT NOT NULL,
    completed INTEGER DEFAULT 0
)
"""

# SQL to create timer_logs table
CREATE_TIMER_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS timer_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    duration_minutes INTEGER,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
"""


async def init_db():
    """Initialize database and create tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TASKS_TABLE)
        await db.execute(CREATE_TIMER_LOGS_TABLE)
        await db.commit()
    print(f"[DB] Database initialized at {DB_PATH}")


async def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all tasks from database"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Get a single task by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new task"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO tasks (id, title, description, deadline, priority, dependencies, recurring, recurring_interval, created_at, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_data["id"],
                task_data["title"],
                task_data.get("description", ""),
                task_data.get("deadline"),
                task_data.get("priority", "Medium"),
                task_data.get("dependencies", []),
                1 if task_data.get("recurring") else 0,
                task_data.get("recurring_interval", "Daily"),
                task_data.get("created_at"),
                1 if task_data.get("completed") else 0
            )
        )
        await db.commit()
    return task_data


async def update_task(task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing task"""
    set_clauses = []
    values = []
    
    for key, value in updates.items():
        if key == "completed":
            set_clauses.append("completed = ?")
            values.append(1 if value else 0)
        elif key == "dependencies":
            set_clauses.append("dependencies = ?")
            values.append(str(value))
        elif key == "recurring":
            set_clauses.append("recurring = ?")
            values.append(1 if value else 0)
        else:
            set_clauses.append(f"{key} = ?")
            values.append(value)
    
    if not set_clauses:
        return await get_task_by_id(task_id)
    
    values.append(task_id)
    query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, values)
        await db.commit()
    
    return await get_task_by_id(task_id)


async def delete_task(task_id: str) -> bool:
    """Delete a task"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
    return True


async def log_timer_session(task_id: str, duration_minutes: int) -> int:
    """Log a timer session start"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO timer_logs (task_id, duration_minutes, started_at, completed)
            VALUES (?, ?, ?, 0)
            """,
            (task_id, duration_minutes, datetime.now().isoformat())
        )
        await db.commit()
        return cursor.lastrowid


async def complete_timer_session(log_id: int) -> bool:
    """Mark timer session as completed"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE timer_logs SET ended_at = ?, completed = 1 WHERE id = ?",
            (datetime.now().isoformat(), log_id)
        )
        await db.commit()
    return True


async def get_timer_stats() -> Dict[str, Any]:
    """Get timer statistics"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Total completed sessions
        async with db.execute("SELECT COUNT(*) as count FROM timer_logs WHERE completed = 1") as cursor:
            completed = (await cursor.fetchone())[0]
        
        # Total time spent
        async with db.execute("SELECT SUM(duration_minutes) as total FROM timer_logs WHERE completed = 1") as cursor:
            total_time = (await cursor.fetchone())[0] or 0
        
        # Today's sessions
        today = datetime.now().strftime("%Y-%m-%d")
        async with db.execute(
            "SELECT COUNT(*) as count FROM timer_logs WHERE completed = 1 AND started_at LIKE ?",
            (f"{today}%",)
        ) as cursor:
            today_count = (await cursor.fetchone())[0]
        
        return {
            "total_completed": completed,
            "total_minutes": total_time,
            "today_completed": today_count
        }