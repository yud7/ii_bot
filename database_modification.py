import aiosqlite
import sqlite3
from datetime import datetime

async def initialize_db():
    """
    Создаёт (или обновляет) таблицу users, если она ещё не существует.
    Добавляет поля last_5min_reminder, last_24h_reminder и notification при необходимости.
    """
    async with aiosqlite.connect("users.db") as db:
        # Создаём таблицу, если её нет.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                notification TEXT,          -- Поле для включения/выключения уведомлений
                last_activity DATETIME,
                last_5min_reminder DATETIME,
                last_24h_reminder DATETIME
            )
        """)
        await db.commit()

        # Если таблица уже существует, но без нужных полей, добавляем их:
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_5min_reminder DATETIME")
        except sqlite3.OperationalError:
            pass

        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_24h_reminder DATETIME")
        except sqlite3.OperationalError:
            pass

        try:
            await db.execute("ALTER TABLE users ADD COLUMN notification TEXT")
        except sqlite3.OperationalError:
            pass

        await db.commit()


async def get_user_by_id(telegram_id: int):
    """
    Возвращает всю строку (кортеж) с данными о пользователе по Telegram ID.
    Или None, если пользователь не найден.
    """
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("""
            SELECT * FROM users WHERE telegram_id = ?
        """, (telegram_id,)) as cursor:
            return await cursor.fetchone()


async def insert_user(telegram_id: int, first_name: str, last_name: str, age: int):
    """
    Добавляет нового пользователя в базу.
    По умолчанию ставим notification = 'True', чтобы сразу получать уведомления.
    """
    async with aiosqlite.connect("users.db") as db:
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
            'True',                      # <-- По умолчанию True
            datetime.now().isoformat(),
            None,
            None
        ))
        await db.commit()


async def update_last_activity(telegram_id: int):
    """
    Обновляет поле last_activity пользователя (время последнего действия).
    """
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            UPDATE users
            SET last_activity = ?
            WHERE telegram_id = ?
        """, (datetime.now().isoformat(), telegram_id))
        await db.commit()


async def set_notifications_enabled(telegram_id: int, enabled: bool):
    """
    Включает или выключает уведомления пользователю с заданным telegram_id.
    notification='True' или 'False'.
    """
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            UPDATE users
            SET notification = ?
            WHERE telegram_id = ?
        """, ('True' if enabled else 'False', telegram_id))
        await db.commit()