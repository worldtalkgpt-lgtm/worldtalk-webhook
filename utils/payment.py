import os
from urllib.parse import urlencode

# ID готовой платёжной формы (в CloudPayments -> Платёжные ссылки)
CP_LINK_ID = os.getenv("CLOUDPAYMENTS_LINK_ID", "578864fc4bb04b65baf266cdae862fa7")

BASE_URL = f"https://c.cloudpayments.ru/payments/{CP_LINK_ID}"

def build_payment_link_lite(telegram_id: int) -> str:
    """
    Возвращает одну и ту же платёжную ссылку CP,
    но с привязкой пользователя через accountId.
    """
    qs = urlencode({
        "accountId": str(telegram_id),
        # можно передавать метки, если хочется:
        "tariff": "Lite",
        "voices": 100,
    })
    return f"{BASE_URL}?{qs}"
