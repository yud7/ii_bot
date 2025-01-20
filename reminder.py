import asyncio
import configparser
import logging
from datetime import datetime, timedelta

import aiosqlite
from aiogram import Bot

logging.basicConfig(level=logging.INFO)


async def send_reminders():
    """
    Периодически (раз в 60 секунд) проверяет, когда пользователи были активны,
    и отправляет им напоминания:
      - Через 1 минуту после последней активности
      - Через 24 часа после последней активности

    Отправка происходит только при условии notification = 'True'.
    """
    config = configparser.ConfigParser()
    config.read("config.ini")
    bot_token = config.get("default", "botToken")

    bot = Bot(token=bot_token)
    print("reminder started")

    while True:
        try:
            async with aiosqlite.connect("users.db") as db:
                # Достаём необходимые поля, включая notification
                cursor = await db.execute("""
                    SELECT telegram_id, last_activity,
                           last_5min_reminder, last_24h_reminder,
                           notification
                    FROM users
                """)
                rows = await cursor.fetchall()

                for row in rows:
                    telegram_id = row[0]
                    last_activity_str = row[1]
                    last_5min_str = row[2]
                    last_24h_str = row[3]
                    notification_str = row[4]  # 'True' или 'False'

                    # Если пользователь отключил уведомления, пропускаем
                    if notification_str == 'False':
                        continue

                    # Если нет данных о последней активности, пропускаем
                    if not last_activity_str:
                        continue

                    now = datetime.now()
                    last_activity = datetime.fromisoformat(last_activity_str)

                    # --- Напоминание через 1 минуту ---
                    if (now - last_activity) >= timedelta(minutes=1):
                        send_1min = False

                        if not last_5min_str:
                            # Никогда не отправляли 1-минутное уведомление
                            send_1min = True
                        else:
                            last_5min_reminder = datetime.fromisoformat(last_5min_str)
                            # Если последнее 1-минутное уведомление было до новой активности
                            if last_5min_reminder < last_activity:
                                send_1min = True

                        if send_1min:
                            try:
                                await bot.send_message(
                                    chat_id=telegram_id,
                                    text="Прошла 1 минута с вашей последней активности. Напоминаем о тесте!"
                                )
                                # Обновляем метку, чтобы не слать повторно
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

        # Ждём 60 секунд до следующей проверки
        await asyncio.sleep(60)

async def main():
    await send_reminders()

if __name__ == "__main__":
    asyncio.run(main())