from aiogram import types
from aiogram.dispatcher import Dispatcher

def register_handlers(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "buy")
    async def show_purchase_callback(callback_query: types.CallbackQuery):
        await send_purchase_screen(callback_query.message, is_callback=True)

    @dp.message_handler(commands=["buy"])
    async def show_purchase_command(message: types.Message):
        await send_purchase_screen(message)

async def send_purchase_screen(target, is_callback=False):
    text = (
        "💎 <b>Покупка голосов</b>\n\n"
        "Открой голоса легенд.  \n"
        "Выбирай свой путь:\n\n"
        "🔹 200 голосов — <b>329₽</b>\n"
        "🔸 500 голосов — <b>590₽</b>\n"
        "🔷 1000 голосов — <b>890₽</b>\n\n"
        "🗣 <i>1 голос = 1 реплика персонажа</i>\n"
        "🕓 <i>Голоса не сгорают</i>"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("200 голосов — 329₽", callback_data="buy_200"),
        types.InlineKeyboardButton("500 голосов — 590₽", callback_data="buy_500"),
        types.InlineKeyboardButton("1000 голосов — 890₽", callback_data="buy_1000")
    )

    if is_callback:
        await target.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
