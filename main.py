import asyncio
import sys
import subprocess

from handlers import start_bot

if __name__ == '__main__':

    # subprocess.Popen([sys.executable, "reminder.py"])
    asyncio.run(start_bot())
