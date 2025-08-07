from db.base import Base
from models.user import User
from db.session import engine  # важно: это должен быть твой асинхронный движок, как в боте

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_tables())
