import hmac
import base64
import json
from hashlib import sha256
from aiohttp import web
from user_repo import add_voices  # твоя функция из user_repo.py
import os

CLOUDPAYMENTS_API_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET")

async def cloudpayments_webhook(request):
    try:
        data = await request.post()
        raw_body = await request.text()

        # 1️⃣ Проверка подписи
        signature = request.headers.get("Content-HMAC", "")
        computed_hmac = base64.b64encode(
            hmac.new(
                CLOUDPAYMENTS_API_SECRET.encode("utf-8"),
                raw_body.encode("utf-8"),
                sha256
            ).digest()
        ).decode("utf-8")

        if not hmac.compare_digest(signature, computed_hmac):
            return web.json_response({"code": 13})  # Ошибка авторизации

        # 2️⃣ Обработка типов уведомлений
        event = data.get("InvoiceId")
        amount = float(data.get("Amount", 0))
        user_id = int(data.get("AccountId", 0))
        notification_type = request.path.split("/")[-1]

        # На "Check" просто подтверждаем
        if data.get("Status") is None and request.method == "POST":
            return web.json_response({"code": 0})

        # На Pay — начисляем голоса
        if amount == 149:
            await add_voices(user_id, 100)
            return web.json_response({"code": 0})

        return web.json_response({"code": 0})

    except Exception as e:
        print(f"Webhook error: {e}")
        return web.json_response({"code": 13})

app = web.Application()
app.router.add_post("/cloudpayments/webhook", cloudpayments_webhook)

if __name__ == "__main__":
    web.run_app(app, port=5000)
