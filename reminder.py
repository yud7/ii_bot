import asyncio
import logging
import configparser
import aiosqlite
from datetime import datetime, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read("config.ini")
bot_token = config.get('default', 'botToken')
bot = Bot(token=bot_token)


async def check_inactive_users():
    """
    Пример функции, которую APScheduler вызывает по расписанию.
    Здесь проверяется, кто 2+ минуты не писал боту.
    """
    now = datetime.now()
    two_minutes_ago = now - timedelta(minutes=2)
    cutoff_str = two_minutes_ago.isoformat()

    logging.info("Проверяем пользователей на неактивность более 2 минут...")

    try:
        async with aiosqlite.connect("users.db") as db:
            query = """
                SELECT telegram_id, last_activity
                FROM users
                WHERE last_activity IS NOT NULL
                  AND last_activity < ?
            """
            async with db.execute(query, (cutoff_str,)) as cursor:
                rows = await cursor.fetchall()

            for telegram_id, last_act in rows:
                try:
                    await bot.send_message(
                        chat_id=telegram_id,
                        text="Вы не писали 2 минуты! Напоминаю, что я здесь..."
                    )
                    logging.info(f"Отправлено напоминание пользователю {telegram_id}")
                except Exception as e:
                    logging.error(f"Ошибка отправки напоминания {telegram_id}: {e}")

    except Exception as e:
        logging.error(f"Ошибка в check_inactive_users: {e}")


async def main():
    scheduler = AsyncIOScheduler()
    # Каждую минуту запускаем функцию проверки
    scheduler.add_job(check_inactive_users, "interval", minutes=1)
    
    scheduler.start()
    logging.info("Scheduler запущен. Ожидаем события...")

    # Чтобы процесс не завершился, делаем бесконечную "задержку"
    # (либо используйте другой способ «заставить» event loop работать)
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
