from aiohttp import web
import hmac, hashlib, os, json
from dotenv import load_dotenv
from aiogram import Bot

# 👉 добавь эти импорты
from db import async_session            # твоя фабрика сессий
from sqlalchemy import select
from models.processed_payment import ProcessedPayment  # см. модель ниже
from user_repo import add_voices

load_dotenv()

CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

async def cloudpayments_webhook(request: web.Request):
    raw_text = await request.text()
    headers = request.headers

    # CloudPayments иногда шлёт form-urlencoded (в т.ч. в "Проверке уведомлений")
    if (not raw_text.strip()
        and headers.get("Content-Type","").startswith("application/x-www-form-urlencoded")):
        form = await request.post()
        # в этом случае тело JSON лежит в поле Data
        raw_text = form.get("Data", "")

    if not raw_text:
        request.app.logger.error("Empty body from CloudPayments")
        return web.json_response({"code": 13, "message": "Empty body"}, status=400)

    # HMAC подпись
    signature = headers.get("Content-HMAC") or headers.get("Content-Hmac")
    expected = hmac.new(
        CLOUDPAYMENTS_SECRET.encode("utf-8"),
        raw_text.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    if not signature or signature.lower() != expected.lower():
        return web.json_response({"code": 13, "message": "Invalid signature"}, status=403)

    # JSON
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        request.app.logger.exception("Bad JSON")
        return web.json_response({"code": 13, "message": "Bad JSON"}, status=400)

    event = (payload.get("Event") or payload.get("NotificationType") or "").lower()

    # Универсально: и в Check, и в Pay эти поля есть
    account_id = payload.get("AccountId")
    amount = float(payload.get("Amount", 0))
    currency = (payload.get("Currency") or "RUB").upper()
    tx_id = str(payload.get("TransactionId") or "")  # для идемпотентности
    data = payload.get("Data") or {}
    voices = int(data.get("voices", 0))              # мы кладём это в JsonData при формировании ссылки
    tariff = data.get("tariff")

    if event == "check":
        # можно сделать валидацию (например, что сумма/валюта совпадают с тарифом)
        return web.json_response({"code": 0})

    if event == "pay":
        # 1) базовые проверки (подстрои под свой тариф)
        if not account_id or voices <= 0:
            return web.json_response({"code": 13, "message": "bad fields"}, status=400)
        if currency != "RUB":
            return web.json_response({"code": 13, "message": "bad currency"}, status=400)

        # Пример: тариф Lite (100 голосов за 149 ₽)
        # Если тарифов несколько — сделай словарь допустимых сумм/голосов и сверяй.
        if tariff == "lite":
            if not (voices == 100 and abs(amount - 149.0) < 0.01):
                return web.json_response({"code": 13, "message": "bad amount/voices"}, status=400)
        # else: проверки для других тарифов…

        # 2) идемпотентность по TransactionId
        async with async_session() as s:
            if tx_id:
                from sqlalchemy import select
                res = await s.execute(select(ProcessedPayment).where(ProcessedPayment.transaction_id == tx_id))
                if res.scalar_one_or_none():
                    return web.json_response({"code": 0})  # уже обработали

            # 3) начисляем голоса
            await add_voices(s, int(account_id), voices)

            # 4) помечаем транзакцию как обработанную
            if tx_id:
                s.add(ProcessedPayment(transaction_id=tx_id))
            await s.commit()

        # (опционально) уведомим пользователя в TG
        # if bot:
        #     try:
        #         await bot.send_message(int(account_id), f"✅ Оплата {amount:.0f} ₽ прошла. Начислено {voices} голосов.")
        #     except Exception:
        #         request.app.logger.exception("Failed to notify user")

        return web.json_response({"code": 0})

    # на всякий случай — ок на другие эвенты
    return web.json_response({"code": 0})


def create_app():
    app = web.Application()
    app.router.add_post("/cloudpayments/webhook", cloudpayments_webhook)
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
