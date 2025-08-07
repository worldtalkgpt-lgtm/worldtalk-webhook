from sqlalchemy import select
from db import AsyncSessionLocal
from models.user import User

# Создание нового пользователя
async def add_user(telegram_id: int, username: str, full_name: str):
    async with AsyncSessionLocal() as session:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name
        )
        session.add(user)
        await session.commit()

# Проверка, есть ли пользователь в базе
async def get_user_by_telegram_id(telegram_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
