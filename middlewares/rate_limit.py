import time
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler  # 👈 добавляем

user_last_message = {}

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit_per_sec: float = 1.0):
        super(RateLimitMiddleware, self).__init__()
        self.limit_per_sec = limit_per_sec

    async def on_pre_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        now = time.time()
        last_time = user_last_message.get(user_id, 0)

        if now - last_time < self.limit_per_sec:
            await message.reply("⛔️ Пожалуйста, без спама, я всё вижу.")
            # ❌ Отменяем обработку, чтобы хендлеры дальше не сработали
            raise CancelHandler()

        user_last_message[user_id] = now
