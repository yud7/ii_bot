import aiosqlite
from datetime import datetime


async def initialize_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                notification TEXT,
                last_activity DATETIME
            )
        """)
        await db.commit()


async def get_user_by_id(telegram_id: int):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("""
            SELECT * FROM users WHERE telegram_id = ?
        """, (telegram_id,)) as cursor:
            return await cursor.fetchone()


async def insert_user(telegram_id: int, first_name: str, last_name: str, age: int):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            INSERT INTO users (telegram_id, first_name, last_name, age, notification, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, first_name, last_name, age, 'False', datetime.now().isoformat()))
        await db.commit()


async def update_last_activity(telegram_id: int):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            UPDATE users
            SET last_activity = ?
            WHERE telegram_id = ?
        """, (datetime.now().isoformat(), telegram_id))
        await db.commit()


async def set_notifications_enabled(telegram_id: int, enabled: bool):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            UPDATE users
            SET notification = ?
            WHERE telegram_id = ?
        """, ('True' if enabled else 'False', telegram_id))
        await db.commit()
