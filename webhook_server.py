import os
import json
import hmac
import hashlib
import logging
from decimal import Decimal

from aiohttp import web
from dotenv import load_dotenv

from sqlalchemy.future import select

# === твои зависимости проекта ===
from db.session import async_session  # <-- если у тебя по-другому называется, поправь
from services.user_repo import add_voices
from models.processed_payment import ProcessedPayment

# --- опционально для уведомления в TG, если BOT_TOKEN есть
from aiogram import Bot

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

# рубли -> голоса (фиксируем тарифы)
VOICES_BY_AMOUNT_RUB = {
    149: 100,  # Lite
    # сюда потом добавишь другие тарифы: 299: 250, и т.д.
}


def _calc_signature(raw_text: str) -> str:
    return hmac.new(
        CLOUDPAYMENTS_SECRET.encode("utf-8"),
        raw_text.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


async def cloudpayments_webhook(request: web.Request) -> web.Response:
    # 1) читаем "сырое" тело ровно так, как его подписал CloudPayments
    raw_body = await request.read()
    raw_text = raw_body.decode("utf-8", errors="ignore")
    headers = request.headers

    # Иногда CloudPayments присылает форму (Content-Type: application/x-www-form-urlencoded)
    # и полезную нагрузку кладёт в поле "Data"
    if (not raw_text.strip()
            and headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded")):
        form = await request.post()
        raw_text = form.get("Data", "")

    if not raw_text:
        logger.error("Empty body from CloudPayments")
        return web.json_response({"code": 13, "message": "Empty body"}, status=400)

    # 2) валидируем подпись
    signature = headers.get("Content-HMAC") or headers.get("Content-Hmac") or ""
    expected = _calc_signature(raw_text)
    if not signature or signature.lower() != expected.lower():
        logger.warning("Invalid signature")
        return web.json_response({"code": 13, "message": "Invalid signature"}, status=403)

    # 3) парсим JSON
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.exception("Bad JSON")
        return web.json_response({"code": 13, "message": "Bad JSON"}, status=400)

    event = (payload.get("Event") or payload.get("NotificationType") or "").lower()
    account_id = str(payload.get("AccountId") or "")
    transaction_id = str(payload.get("TransactionId") or payload.get("Id") or "")

    logger.info(f"Webhook event={event} tx={transaction_id} account={account_id}")

    # 4) CloudPayments "check" — отвечаем ОК, иначе платёж не пройдёт
    if event == "check":
        return web.json_response({"code": 0})

    # 5) Успешная оплата
    if event == "pay":
        # Берём сумму/валюту
        try:
            amount = Decimal(str(payload.get("Amount", "0")))
        except Exception:
            amount = Decimal("0")
        currency = (payload.get("Currency") or "RUB").upper()

        # Нормализуем до целых рублей (149.00 -> 149)
        rub_int = int(round(float(amount)))

        voices_to_add = 0
        if currency == "RUB":
            voices_to_add = VOICES_BY_AMOUNT_RUB.get(rub_int, 0)

        if not account_id.isdigit():
            # Если не смогли понять пользователя — просто подтвердим,
            # чтобы CloudPayments не ретраил бесконечно, и залогируем
            logger.error(f"PAY without valid AccountId: {account_id}")
            return web.json_response({"code": 0})

        if voices_to_add <= 0:
            logger.warning(f"No voices mapping for amount={rub_int} {currency}")
            return web.json_response({"code": 0})

        # 6) антидубль: один и тот же TransactionId может прийти несколько раз
        async with async_session() as session:
            exists = await session.get(ProcessedPayment, transaction_id) if transaction_id else None
            if exists:
                return web.json_response({"code": 0})

            # начисляем голоса
            await add_voices(session, int(account_id), voices_to_add)

            # фиксируем обработку транзакции
            session.add(ProcessedPayment(
                transaction_id=transaction_id or f"noid-{account_id}-{rub_int}",
                account_id=account_id,
                amount=int(amount * 100),  # копейки, если нужно
            ))
            await session.commit()

        # можно отправить уведомление в TG (по желанию)
        if bot:
            try:
                await bot.send_message(
                    int(account_id),
                    f"✅ Оплата прошла, начислено {voices_to_add} голосов. Спасибо!"
                )
            except Exception:
                pass

        return web.json_response({"code": 0})

    # На остальные эвенты отвечаем ОК, чтобы не спамило ретраями
    return web.json_response({"code": 0})


# простой healthcheck
async def health(_):
    return web.json_response({"ok": True})


def create_app():
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post("/cloudpayments/webhook", cloudpayments_webhook)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
