# webhook_server.py

from aiohttp import web
import os, hmac, hashlib, json
from db.session import get_session
from db.user_repo import add_voices
from dotenv import load_dotenv

load_dotenv()
CLOUDPAYMENTS_SECRET = os.getenv("CLOUDPAYMENTS_API_SECRET")

routes = web.RouteTableDef()

@routes.post("/cloudpayments/webhook")
async def handle_webhook(request):
    try:
        raw_data = await request.read()
        data = json.loads(raw_data)

        # Подпись запроса
        signature = request.headers.get("Content-HMAC", "")
        expected_signature = hmac.new(
            key=CLOUDPAYMENTS_SECRET.encode(),
            msg=raw_data,
            digestmod=hashlib.sha256
        ).hexdigest()

        if signature != expected_signature:
            return web.json_response({"code": 13, "message": "Invalid HMAC"}, status=403)

        user_id = int(data.get("AccountId"))
        amount = float(data.get("Amount", 0))

        # Сопоставление суммы -> количество голосов
        voices_map = {10: 10, 149: 100, 249: 250, 379: 500}
        voices = voices_map.get(int(amount), 0)

        if voices == 0:
            return web.json_response({"code": 0, "message": "Unsupported amount"})

        async with get_session() as session:
            await add_voices(session, user_id, voices)

        return web.json_response({"code": 0})
    
    except Exception as e:
        return web.json_response({"code": 99, "message": str(e)}, status=500)

app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, port=int(os.getenv("PORT", 8000)))