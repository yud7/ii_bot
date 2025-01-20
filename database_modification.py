import aiosqlite
from datetime import datetime
import sqlite3


async def initialize_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                notification TEXT DEFAULT 'True',
                last_activity DATETIME
                last_5min_reminder DATETIME
                last_24h_reminder DATETIME
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                test_topic TEXT,
                correct_answers INTEGER,
                total_questions INTEGER,
                test_date DATETIME
            )
        """)
        await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER,
                        rating INTEGER,
                        positive_feedback TEXT,
                        negative_feedback TEXT,
                        review_date DATETIME
                    )
                """)
        await db.commit()
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_5min_reminder DATETIME")
        except sqlite3.OperationalError:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_24h_reminder DATETIME")
        except sqlite3.OperationalError:
            pass


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
        """, (telegram_id, first_name, last_name, age, 'True', datetime.now().isoformat()))
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


async def insert_test_result(telegram_id: int, topic: str, correct_answers: int, total_questions: int):
    """
    Inserts a test result into the user_statistics table.
    """
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            INSERT INTO user_statistics (
                telegram_id, test_topic, correct_answers, total_questions, test_date
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            telegram_id, topic, correct_answers, total_questions, datetime.now().isoformat()
        ))
        await db.commit()


async def get_user_statistics(telegram_id: int):
    """
    Fetches all test statistics for a user.
    """
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("""
            SELECT test_topic, correct_answers, total_questions, test_date
            FROM user_statistics
            WHERE telegram_id = ?
            ORDER BY test_date DESC
        """, (telegram_id,)) as cursor:
            return await cursor.fetchall()


async def get_all_users():
    """
    Fetches all users and their fields from the database.
    """
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("""
            SELECT telegram_id, last_activity, last_5min_reminder, last_24h_reminder, notification
            FROM users
        """) as cursor:
            return await cursor.fetchall()


async def save_review_to_database(
    user_id: int,
    rating: int,
    positive_feedback: str,
    negative_feedback: str
):
    """
    Сохраняет отзыв пользователя в таблице user_reviews.
    """
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            INSERT INTO user_reviews (
                telegram_id, rating, positive_feedback, negative_feedback, review_date
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id, rating, positive_feedback, negative_feedback, datetime.now().isoformat()
        ))
        await db.commit()