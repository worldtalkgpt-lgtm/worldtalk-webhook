from aiohttp import web
import hmac
import hashlib
import os
import json
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)

async def handle_webhook(request):
    try:
        raw_body = await request.read()
        headers = request.headers

        # Проверка подписи CloudPayments
        signature = headers.get('Content-HMAC', '')
        expected_signature = hmac.new(
            CLOUDPAYMENTS_SECRET.encode(),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return web.json_response({'code': 13, 'message': 'Invalid signature'}, status=403)

        payload = json.loads(raw_body.decode())
        print("✅ PAYLOAD:", payload)

        # Обработка платежа
        if payload.get("Status") == "Completed":
            amount = float(payload.get("Amount", 0))
            user_id = payload.get("AccountId")  # Это chat_id из ссылки

            if user_id:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"💳 Платеж на {amount} руб. успешно зачислен! Спасибо!"
                )
                print(f"✅ Уведомление отправлено пользователю {user_id}")

        return web.json_response({'code': 0})

    except Exception as e:
        print("❌ Ошибка:", e)
        return web.json_response({'code': 500, 'message': str(e)}, status=500)

app = web.Application()
app.router.add_post("/cloudpayments/webhook", handle_webhook)

if __name__ == '__main__':
    web.run_app(app, port=10000)