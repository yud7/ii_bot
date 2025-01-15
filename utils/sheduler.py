from apscheduler.schedulers.asyncio import AsyncIOScheduler

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler()

    # Пример задачи
    async def send_reminder():
        await bot.send_message(chat_id=123456789, text="Напоминание!")

    scheduler.add_job(send_reminder, "interval", hours=1)
    scheduler.start()
