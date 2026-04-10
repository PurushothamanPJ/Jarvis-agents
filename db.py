import aiosqlite
from datetime import datetime

DB_PATH = "jarvis.db"

async def init_db():
    """Create the tasks table if it doesn't exist and add new columns"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create table with old schema first
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                user_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        # Add new columns if they don't exist
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'")
        except aiosqlite.OperationalError:
            pass  # Column already exists
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN agent TEXT NOT NULL DEFAULT 'discord-interface'")
        except aiosqlite.OperationalError:
            pass
        try:
            await db.execute("ALTER TABLE tasks ADD COLUMN result TEXT")
        except aiosqlite.OperationalError:
            pass
        await db.commit()

async def create_task(command: str, user_id: str, channel_id: str, agent: str):
    """Create a new task record and return the task_id"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tasks (command, user_id, channel_id, created_at, status, agent, result) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (command, user_id, channel_id, datetime.utcnow().isoformat(), "received", agent, None)
        )
        task_id = cursor.lastrowid
        await db.commit()
        return task_id

async def complete_task(task_id: int, result: str):
    """Mark a task as completed with result"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET status = 'completed', result = ? WHERE id = ?",
            (result, task_id)
        )
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
            "SELECT id, command, user_id, channel_id, created_at, status, agent, result FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return rows
