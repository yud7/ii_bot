# main.py
import asyncio
import sys
import subprocess

from handlers import start_bot

if __name__ == '__main__':
    # 1. Запускаем скрипт reminder.py в отдельном процессе
    subprocess.Popen([sys.executable, "reminder.py"])

    # 2. Запускаем бота (polling) в текущем процессе
    asyncio.run(start_bot())