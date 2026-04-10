import aiosqlite
from datetime import datetime

DB_PATH = "jarvis.db"

async def init_db():
    """Create the tasks table if it doesn't exist"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                user_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def log_task(command: str, user_id: str, channel_id: str):
    """Insert a task record into the database"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tasks (command, user_id, channel_id, created_at) VALUES (?, ?, ?, ?)",
            (command, user_id, channel_id, datetime.utcnow().isoformat())
        )
        await db.commit()

async def get_last_tasks(limit: int = 5):
    """Get the last N task records"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, command, user_id, channel_id, created_at FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return rows
