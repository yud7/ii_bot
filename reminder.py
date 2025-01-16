# reminder.py
import asyncio
import configparser
import logging
from datetime import datetime, timedelta

import aiosqlite
from aiogram import Bot

logging.basicConfig(level=logging.INFO)

async def send_reminders():
    """
    Периодически проверяет, когда пользователи были активны,
    и отправляет им напоминания:
      - Через 1 минуту после последней активности
      - Через 24 часа после последней активности
    """
    # Загружаем токен бота из config.ini
    config = configparser.ConfigParser()
    config.read("config.ini")
    bot_token = config.get("default", "botToken")

    bot = Bot(token=bot_token)
    print("reminder started")
    while True:
        try:
            async with aiosqlite.connect("users.db") as db:
                # Получаем пользователей и их метки активности/уведомлений
                cursor = await db.execute("""
                    SELECT telegram_id, last_activity, last_5min_reminder, last_24h_reminder
                    FROM users
                """)
                rows = await cursor.fetchall()

                for row in rows:
                    telegram_id = row[0]
                    last_activity_str = row[1]
                    last_5min_str = row[2]   # Используем ту же колонку, что была "5 минут"
                    last_24h_str = row[3]

                    # Если нет данных о последней активности, пропускаем
                    if not last_activity_str:
                        continue

                    now = datetime.now()
                    last_activity = datetime.fromisoformat(last_activity_str)

                    # --- Напоминание через 1 минуту ---
                    # Если прошло >= 1 минуты с момента последней активности
                    # и ещё не отправляли уведомление после этой самой активности:
                    if (now - last_activity) >= timedelta(minutes=1):
                        send_1min = False

                        if not last_5min_str:
                            # Никогда не отправляли уведомление «через 1 мин»
                            send_1min = True
                        else:
                            last_5min_reminder = datetime.fromisoformat(last_5min_str)
                            # Проверяем, что предыдущее уведомление было ДО новой активности
                            if last_5min_reminder < last_activity:
                                send_1min = True

                        if send_1min:
                            try:
                                await bot.send_message(
                                    chat_id=telegram_id,
                                    text="Прошла 1 минута с вашей последней активности. Напоминаем о тесте!"
                                )
                                # Ставим время отправки этого уведомления
                                await db.execute("""
                                    UPDATE users
                                    SET last_5min_reminder = ?
                                    WHERE telegram_id = ?
                                """, (now.isoformat(), telegram_id))
                                await db.commit()
                            except Exception as e:
                                logging.error(f"[1 min] Ошибка отправки уведомления пользователю {telegram_id}: {e}")

                    # --- Напоминание через 24 часа ---
                    if (now - last_activity) >= timedelta(hours=24):
                        send_24h = False

                        if not last_24h_str:
                            # Никогда не отправляли уведомление «через 24 ч»
                            send_24h = True
                        else:
                            last_24h_reminder = datetime.fromisoformat(last_24h_str)
                            if last_24h_reminder < last_activity:
                                send_24h = True

                        if send_24h:
                            try:
                                await bot.send_message(
                                    chat_id=telegram_id,
                                    text="Прошли сутки с вашей последней активности. Напоминаем о тесте!"
                                )
                                # Ставим время отправки этого уведомления
                                await db.execute("""
                                    UPDATE users
                                    SET last_24h_reminder = ?
                                    WHERE telegram_id = ?
                                """, (now.isoformat(), telegram_id))
                                await db.commit()
                            except Exception as e:
                                logging.error(f"[24h] Ошибка отправки уведомления пользователю {telegram_id}: {e}")

        except Exception as e:
            logging.error(f"Ошибка в цикле отправки напоминаний: {e}")

        # Ждем 60 секунд до следующей проверки
        await asyncio.sleep(60)


async def main():
    await send_reminders()


if __name__ == "__main__":
    asyncio.run(main())