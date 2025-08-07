import asyncio
from sqlalchemy import update
from db.session import get_session
from models.user import User  # Импортируй свою модель User

async def reset_referral_counts():
    async with get_session() as session:
        await session.execute(
            update(User).values(invited_this_week=0)
        )
        await session.commit()
        print("✅ Все счётчики приглашений сброшены.")

if __name__ == "__main__":
    asyncio.run(reset_referral_counts())
