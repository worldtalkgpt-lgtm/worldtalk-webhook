from aiohttp import web
import hmac, hashlib, os, json
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
bot = Bot(token=BOT_TOKEN)

async def cloudpayments_webhook(request: web.Request):
    # читаем как текст
    raw_text = await request.text()
    headers = request.headers

    # если пришло как form-urlencoded — берем поле Data
    if not raw_text.strip() and headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
        form = await request.post()
        raw_text = form.get("Data", "")

    if not raw_text:
        # логируем и отвечаем «плохо», чтобы понять что именно прилетает
        request.app.logger.error("Empty body from CloudPayments")
        return web.json_response({"code": 13, "message": "Empty body"}, status=400)

    # проверяем подпись (хедер может называться по-разному)
    signature = headers.get("Content-HMAC") or headers.get("Content-Hmac") or headers.get("Content-Hmac".lower())
    expected = hmac.new(CLOUDPAYMENTS_SECRET.encode("utf-8"),
                        raw_text.encode("utf-8"),
                        hashlib.sha256).hexdigest()

    if not signature or signature.lower() != expected.lower():
        return web.json_response({"code": 13, "message": "Invalid signature"}, status=403)

    # парсим JSON
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        request.app.logger.exception("Bad JSON")
        return web.json_response({"code": 13, "message": "Bad JSON"}, status=400)

    # Определяем тип события (Check/Pay)
    event = payload.get("Event") or payload.get("NotificationType") or headers.get("X-Cloudpayments-Event", "")
    account_id = payload.get("AccountId")  # тут твой Telegram user_id

    # --- Check: всегда отвечаем OK, иначе форма скажет «платеж не может быть принят»
    if str(event).lower() == "check" or ("TransactionId" not in payload and "PaymentUrl" not in payload):
        return web.json_response({"code": 0})

    # --- Pay: зачисляем голоса (если нужно — доп.проверки суммы)
    if str(event).lower() == "pay" or "TransactionId" in payload:
        # TODO: добавить проверку суммы payload.get("Amount") == 149.00
        try:
            # здесь вызов add_voices(session, int(account_id), 100)
            pass
        except Exception:
            request.app.logger.exception("Failed to credit voices")
        return web.json_response({"code": 0})

    # дефолт
    return web.json_response({"code": 0})
