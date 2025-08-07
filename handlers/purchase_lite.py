from aiogram import types
from aiogram.dispatcher import Dispatcher

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "lite_payment")
    async def lite_payment_handler(callback_query: types.CallbackQuery):
        await send_lite_payment_screen(callback_query.message)

async def send_lite_payment_screen(message: types.Message):
    text = (
        "🕯 <b>Тариф Lite</b>\n\n"
        "• 100 голосов для общения с любыми персонажами\n"
        "• Доступ без ограничений\n"
        "• Срок действия — <b>60 дней</b>\n\n"
        "<b>Стоимость: 149₽</b>"
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("💳 Оплатить картой", url="https://c.cloudpayments.ru/payments/578864fc4bb04b65baf266cdae862fa7"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="buy"))

    await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")