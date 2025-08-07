import asyncio
from db.session import get_session
from db.user_repo import add_voices

async def main():
    user_id = 7005903585  # 🟡 замени на свой Telegram ID
    async with get_session() as session:
        await add_voices(session, user_id, 100)  # +100 голосов

asyncio.run(main())
