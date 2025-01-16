import aiosqlite
import sqlite3
from datetime import datetime

async def initialize_db():
    """
    Creates (or updates) the users table if it doesn't exist or missing columns.
    """
    async with aiosqlite.connect("users.db") as db:
        # Создаём таблицу, если её нет.
        # Добавляем поля last_5min_reminder и last_24h_reminder сразу в CREATE TABLE.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                notification TEXT,
                last_activity DATETIME,
                last_5min_reminder DATETIME,
                last_24h_reminder DATETIME
            )
        """)
        await db.commit()

        # Если таблица уже существовала без новых полей, добавляем их через ALTER TABLE (перехватываем ошибку).
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_5min_reminder DATETIME")
        except sqlite3.OperationalError:
            pass  # колонка уже существует, игнорируем

        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_24h_reminder DATETIME")
        except sqlite3.OperationalError:
            pass  # колонка уже существует, игнорируем

        await db.commit()


async def get_user_by_id(telegram_id: int):
    """
    Fetches a user by Telegram ID.
    """
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("""
            SELECT * FROM users WHERE telegram_id = ?
        """, (telegram_id,)) as cursor:
            return await cursor.fetchone()


async def insert_user(telegram_id: int, first_name: str, last_name: str, age: int):
    """
    Inserts a new user into the database.
    """
    async with aiosqlite.connect("users.db") as db:
        # При вставке ставим last_5min_reminder и last_24h_reminder = NULL,
        # чтобы при первой проверке reminder.py понимал, что ещё не отправляли уведомления.
        await db.execute("""
            INSERT INTO users (
                telegram_id, first_name, last_name, age,
                notification, last_activity,
                last_5min_reminder, last_24h_reminder
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telegram_id,
            first_name,
            last_name,
            age,
            'False',
            datetime.now().isoformat(),
            None,
            None
        ))
        await db.commit()


async def update_last_activity(telegram_id: int):
    """
    Updates the last activity timestamp for a user.
    """
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            UPDATE users
            SET last_activity = ?
            WHERE telegram_id = ?
        """, (datetime.now().isoformat(), telegram_id))
        await db.commit()