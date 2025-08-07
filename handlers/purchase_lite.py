from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound
from urllib.parse import urlencode

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "lite_payment")
    async def lite_payment_handler(callback_query: types.CallbackQuery):
        await send_lite_payment_screen(callback_query.message, callback_query.from_user.id)

async def send_lite_payment_screen(message: types.Message, user_id: int):
    text = (
        "🕯 <b>Тариф Lite</b>\n\n"
        "• 100 голосов для общения с любыми персонажами\n"
        "• Доступ без ограничений\n"
        "• Срок действия — <b>60 дней</b>\n\n"
        "<b>Стоимость: 149₽</b>"
    )

    base = "https://c.cloudpayments.ru/payments/578864fc4bb04b65baf266cdae862fa7"
    qs = urlencode({
        "accountId": str(user_id),  # 👈 важно: именно accountId
        "tariff": "Lite",           # не обязат., просто метка
        "voices": 100               # не обязат., у нас маппинг по сумме
    })
    payment_url = f"{base}?{qs}"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💳 Оплатить картой", url=payment_url))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="buy"))

    try:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except (MessageNotModified, MessageToEditNotFound):
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
