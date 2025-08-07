from aiogram import types
from aiogram.dispatcher import Dispatcher

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "buy_ultra")
    async def show_ultra_screen(callback_query: types.CallbackQuery):
        await send_ultra_screen(callback_query.message)

async def send_ultra_screen(message: types.Message):
    text = (
        " <b>┌ Ultra</b> | 500 голосов — <b>379₽ ┐</b>\n\n"
        "📊 <b>Что входит:</b>\n"
        "• 500 голосов для общения с любыми персонажами\n"
        "• Полный доступ без ограничений\n"
        "• Срок действия голосов — 60 дней\n\n"
        "💡 <i>1 голос = 1 ответ персонажа</i>\n\n"
        "Нажимая «Оплатить», вы соглашаетесь с условиями:\n"
        "<a href='https://world-talk.ru/oferta.html'>Публичной оферты</a>\n"
        "<a href='https://world-talk.ru/politika.html'>Политики конфиденциальности</a>\n\n"
        "Выберите способ оплаты 👇"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("💳 Оплатить картой", callback_data="pay_ultra_card"),
        types.InlineKeyboardButton("⭐ Stars", callback_data="pay_ultra_stars")
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="buy"))

    await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)