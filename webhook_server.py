from aiohttp import web
import hmac, hashlib, os, json
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # может быть пустым
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None  # чтобы не падать, если токена нет

async def cloudpayments_webhook(request: web.Request):
    raw_text = await request.text()
    headers = request.headers

    if not raw_text.strip() and headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
        form = await request.post()
        raw_text = form.get("Data", "")

    if not raw_text:
        request.app.logger.error("Empty body from CloudPayments")
        return web.json_response({"code": 13, "message": "Empty body"}, status=400)

    signature = headers.get("Content-HMAC") or headers.get("Content-Hmac")
    expected = hmac.new(CLOUDPAYMENTS_SECRET.encode("utf-8"),
                        raw_text.encode("utf-8"),
                        hashlib.sha256).hexdigest()
    if not signature or signature.lower() != expected.lower():
        return web.json_response({"code": 13, "message": "Invalid signature"}, status=403)

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        request.app.logger.exception("Bad JSON")
        return web.json_response({"code": 13, "message": "Bad JSON"}, status=400)

    event = (payload.get("Event") or payload.get("NotificationType") or "").lower()
    account_id = payload.get("AccountId")

    if event == "check":
        return web.json_response({"code": 0})

    if event == "pay":
        # TODO: проверить сумму/валюту и начислить голоса
        # например: await add_voices(session, int(account_id), 100)
        return web.json_response({"code": 0})

    return web.json_response({"code": 0})

def create_app():
    app = web.Application()
    app.router.add_post("/cloudpayments/webhook", cloudpayments_webhook)
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
