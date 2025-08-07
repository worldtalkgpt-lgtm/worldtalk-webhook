import os, hmac, hashlib, base64, json, logging
from aiohttp import web

from db.session import get_session
from db.user_repo import add_voices

logging.basicConfig(level=logging.INFO)
routes = web.RouteTableDef()

CP_API_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET", "")

def verify_hmac_base64(raw: bytes, header: str) -> bool:
    if not CP_API_SECRET or not header:
        return False
    digest = hmac.new(CP_API_SECRET.encode("utf-8"), raw, hashlib.sha256).digest()
    calc = base64.b64encode(digest).decode()
    return hmac.compare_digest(calc, header)

@routes.post("/cloudpayments/webhook")
async def cloudpayments_webhook(request: web.Request):
    raw = await request.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        logging.exception("Bad JSON")
        return web.json_response({"code": 13}, status=400)  # формат не ок

    # 1) Проверка подписи
    if not verify_hmac_base64(raw, request.headers.get("Content-HMAC", "")):
        logging.warning("Invalid HMAC")
        return web.json_response({"code": 13}, status=401)

    event = data.get("Event")  # 'Check' | 'Pay' | ...
    amount = float(data.get("Amount", 0) or 0)
    account_id = data.get("AccountId")

    logging.info("CP Event=%s Amount=%s AccountId=%s", event, amount, account_id)

    # 2) Check — подтверждаем, что готовы принять оплату
    if event == "Check":
        return web.json_response({"code": 0})

    # 3) Pay — деньги приняты -> начисляем голоса
    if event == "Pay":
        try:
            user_id = int(account_id) if account_id is not None else None
        except ValueError:
            user_id = None

        if user_id is None:
            logging.error("No AccountId in Pay")
            return web.json_response({"code": 0})  # подтверждаем, но без начисления

        # Маппинг сумм -> голоса (тут твой кейс 149 ₽ -> 100)
        voices_by_amount = {
            149.0: 100,
            249.0: 250,
            379.0: 500,
        }
        voices = voices_by_amount.get(amount, 0)

        if voices > 0:
            async with get_session() as session:
                await add_voices(session, user_id, voices)
            logging.info("Added %s voices to user %s", voices, user_id)
        else:
            logging.warning("Unsupported amount: %s", amount)

        # CloudPayments ждёт code=0 как подтверждение обработки
        return web.json_response({"code": 0})

    # 4) Остальные события пока просто подтверждаем
    return web.json_response({"code": 0})

@routes.get("/")
async def health(_):
    return web.Response(text="OK")

def create_app():
    app = web.Application()
    app.add_routes(routes)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
