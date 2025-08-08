from aiohttp import web
import os, hmac, hashlib, json
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models import ProcessedPayment
from repositories import user_repo  # путь поправь, если у тебя иначе

load_dotenv()

# --- Конфиг ---
CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")
DATABASE_URL = os.getenv("DATABASE_URL")  # тот же URL, что использует бот
BOT_TOKEN = os.getenv("BOT_TOKEN", "")    # не обязателен здесь

# Карта тарифов: сколько голосов начислять при какой сумме
VOICE_PACKS = {
    # amount в рублях -> сколько голосов начислять
    149: 100,
    # можно добавить ещё пакеты позже
}

# --- SQLAlchemy ---
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def _get_session() -> AsyncSession:
    return AsyncSessionLocal()

# --- Вспомогательные функции ---
async def _already_processed(session: AsyncSession, tx_id: int) -> bool:
    row = await session.get(ProcessedPayment, tx_id)
    return row is not None

async def _mark_processed(session: AsyncSession, tx_id: int, account_id: int, amount: int, currency: str):
    session.add(ProcessedPayment(
        id=tx_id,
        account_id=str(account_id),
        amount=amount,
        currency=currency
    ))
    await session.commit()

def _check_signature(raw_body: str, request: web.Request) -> bool:
    sig = request.headers.get("Content-HMAC") or request.headers.get("Content-Hmac")
    if not sig:
        return False
    expected = hmac.new(
        CLOUDPAYMENTS_SECRET.encode("utf-8"),
        raw_body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return sig.lower() == expected.lower()

# --- Основной обработчик ---
async def cloudpayments_webhook(request: web.Request):
    # 1) читаем тело (json или form-encoded)
    raw_text = await request.text()
    if (not raw_text.strip()) and request.headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
        form = await request.post()
        raw_text = form.get("Data", "") or ""

    if not raw_text:
        request.app.logger.error("Empty body")
        return web.json_response({"code": 13, "message": "Empty body"}, status=400)

    # 2) проверяем подпись
    if not _check_signature(raw_text, request):
        return web.json_response({"code": 13, "message": "Invalid signature"}, status=403)

    # 3) парсим JSON CloudPayments
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        request.app.logger.exception("Bad JSON")
        return web.json_response({"code": 13, "message": "Bad JSON"}, status=400)

    event = (payload.get("Event") or payload.get("NotificationType") or "").lower()
    account_id = payload.get("AccountId")  # мы кладём сюда telegram_id
    amount = payload.get("Amount")
    currency = (payload.get("Currency") or "RUB").upper()
    tx_id = payload.get("TransactionId") or payload.get("InvoiceId")

    # CloudPayments ждёт ответ даже если нам событие не нужно
    if event == "check":
        return web.json_response({"code": 0})

    if event == "pay":
        # в бою лучше дополнительно валидировать валюту
        if currency != "RUB":
            return web.json_response({"code": 13, "message": "Unsupported currency"}, status=400)

        # округляем сумму до целых рублей на всякий случай
        try:
            amount_rub = int(round(float(amount)))
        except Exception:
            return web.json_response({"code": 13, "message": "Bad amount"}, status=400)

        voices = VOICE_PACKS.get(amount_rub)
        if not voices:
            # неизвестная сумма — не начисляем, но отвечаем 0, чтобы у клиента оплата прошла
            request.app.logger.warning(f"Unknown amount {amount_rub} RUB for account {account_id}")
            return web.json_response({"code": 0})

        if not account_id:
            request.app.logger.error("Missing AccountId")
            return web.json_response({"code": 13, "message": "Missing AccountId"}, status=400)

        if not tx_id:
            request.app.logger.error("Missing TransactionId")
            return web.json_response({"code": 13, "message": "Missing TransactionId"}, status=400)

        # 4) транзакция: защитимся от повторных уведомлений
        async with await _get_session() as session:
            if await _already_processed(session, int(tx_id)):
                return web.json_response({"code": 0})

            # начисляем голоса пользователю
            await user_repo.add_voices(session, int(account_id), voices)

            # фиксируем транзакцию
            await _mark_processed(session, int(tx_id), int(account_id), amount_rub, currency)

        return web.json_response({"code": 0})

    # прочие события нам пока не нужны
    return web.json_response({"code": 0})

def create_app():
    app = web.Application()
    app.router.add_post("/cloudpayments/webhook", cloudpayments_webhook)
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
