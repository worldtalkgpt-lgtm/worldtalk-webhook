import os
import uuid
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

CLOUDPAYMENTS_PUBLIC_ID = os.getenv("CLOUDPAYMENTS_PUBLIC_ID")
CLOUDPAYMENTS_SECRET_KEY = os.getenv("CLOUDPAYMENTS_API_SECRET")

# ⚙️ Генерация Base64 авторизации
CLOUDPAYMENTS_BASIC_AUTH = base64.b64encode(
    f"{CLOUDPAYMENTS_PUBLIC_ID}:{CLOUDPAYMENTS_SECRET_KEY}".encode()
).decode()

# 💳 Генерация платёжной ссылки
def generate_payment_button(label: str, amount: int, user_id: int):
    url = "https://api.cloudpayments.ru/bills/create"

    invoice_id = str(uuid.uuid4())
    payload = {
        "Amount": amount,
        "Currency": "RUB",
        "InvoiceId": invoice_id,
        "Description": f"{label} — Покупка голосов в WorldTalk",
        "AccountId": str(user_id),
        "Email": "",  # можно оставить пустым
        "Skin": "mini",
        "Data": {
            "type": label,
            "user_id": user_id
        }
    }

    headers = {
        "Authorization": f"Basic {CLOUDPAYMENTS_BASIC_AUTH}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()

    if not response_data.get("Success"):
        raise Exception(response_data.get("Message", "Ошибка при создании платёжной ссылки"))

    payment_url = response_data["Model"]["Url"]
    return payment_url, invoice_id