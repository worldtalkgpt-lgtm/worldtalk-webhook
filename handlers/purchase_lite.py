import os
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound

# Загружаем ID ссылки из переменных окружения
LINK_ID = os.getenv("CLOUDPAYMENTS_LITE_LINK_ID")

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

    # Ссылка CloudPayments с привязкой к конкретному пользователю
    payment_url = f"https://c.cloudpayments.ru/payments/{LINK_ID}?AccountId={user_id}"

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💳 Оплатить картой", url=payment_url))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="buy"))

    try:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except (MessageNotModified, MessageToEditNotFound):
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
