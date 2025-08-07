import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

import asyncio
from session import engine, Base
from models.user import User

async def add_test_user():
    async with sessionmaker()() as session:
        user = User(user_id=123456789, username="testuser", voices=10)
        session.add(user)
        await session.commit()
        print("✅ Тестовый пользователь добавлен!")

if __name__ == "__main__":
    asyncio.run(add_test_user())
