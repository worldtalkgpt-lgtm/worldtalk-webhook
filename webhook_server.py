from aiohttp import web
import os, hmac, hashlib, json
from dotenv import load_dotenv

# ✅ твоя функция начисления голосов
# ПОПРАВЬ путь, если user_repo лежит в другом модуле
from services.user_repo import add_voices

load_dotenv()

CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")

# сколько голосов даём за покупку Lite
VOICES_PER_PURCHASE = 100

async def cloudpayments_webhook(request: web.Request):
    # ----- читаем тело так, как присылает CloudPayments -----
    raw_body = await request.text()
    headers = request.headers

    # Если пришло form-encoded (иногда так бывает), берём поле Data
    if (not raw_body.strip()) and headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
        form = await request.post()
        raw_body = form.get("Data", "")

    if not raw_body:
        request.app.logger.error("Empty body from CloudPayments")
        return web.json_response({"code": 13, "message": "Empty body"}, status=400)

    # ----- проверяем подпись HMAC -----
    signature = headers.get("Content-HMAC") or headers.get("Content-Hmac") or headers.get("Content-hmac")
    expected = hmac.new(
        CLOUDPAYMENTS_SECRET.encode("utf-8"),
        raw_body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not signature or signature.lower() != expected.lower():
        return web.json_response({"code": 13, "message": "Invalid signature"}, status=403)

    # ----- парсим JSON -----
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        request.app.logger.exception("Bad JSON")
        return web.json_response({"code": 13, "message": "Bad JSON"}, status=400)

    event = (payload.get("Event") or payload.get("NotificationType") or "").lower()
    account_id = payload.get("AccountId")  # мы передаём сюда telegram_id в ссылке оплаты

    # CloudPayments ждёт 200/{"code":0} на Check
    if event == "check":
        return web.json_response({"code": 0})

    if event == "pay":
        # тут можно дополнительно проверить сумму/валюту при желании:
        # amount = float(payload.get("Amount", 0))
        # currency = payload.get("Currency", "RUB")
        # if amount == 149 and currency == "RUB": ...

        try:
            user_id = int(account_id)
        except (TypeError, ValueError):
            request.app.logger.error(f"Bad AccountId: {account_id}")
            return web.json_response({"code": 13, "message": "Bad AccountId"}, status=400)

        # ✅ Начисляем голоса
        # add_voices(session, user_id, amount) — твоя функция уже инкапсулирует сессию?
        # Если она требует сессию, используй свой helper создания AsyncSession (как в проекте).
        await add_voices(user_id=user_id, amount=VOICES_PER_PURCHASE)  # <-- если у тебя сигнатура другая, поправь

        return web.json_response({"code": 0})

    # Для остальных событий просто ok
    return web.json_response({"code": 0})

def create_app():
    app = web.Application()
    app.router.add_post("/cloudpayments/webhook", cloudpayments_webhook)
    return app

if name == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
