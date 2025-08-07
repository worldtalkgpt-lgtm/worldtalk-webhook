import asyncio
from db_utils import add_user, get_user_by_telegram_id

async def run():
    telegram_id = 707603442  # ← твой Telegram ID
    username = "ivan"        # ← замени на свой username, если хочешь
    full_name = "Иван"       # ← имя, которое будет отображаться

    user = await get_user_by_telegram_id(telegram_id)
    if user:
        print("✅ Ты уже в базе WorldTalk!")
    else:
        await add_user(telegram_id, username, full_name)
        print("🎉 Добро пожаловать в базу WorldTalk!")

asyncio.run(run())
