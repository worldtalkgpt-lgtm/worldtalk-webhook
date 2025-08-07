import sys
import os
import asyncio

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from db.session import get_session
from db.user_repo import reset_weekly_invited

async def main():
    async with get_session() as session:
        await reset_weekly_invited(session)
        print("✅ invited_this_week сброшено у всех пользователей")

if __name__ == "__main__":
    asyncio.run(main())
