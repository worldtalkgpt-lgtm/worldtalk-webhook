from aiogram import types
from aiogram.dispatcher import Dispatcher

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "buy")
    async def show_purchase_callback(callback_query: types.CallbackQuery):
        await send_purchase_screen(callback_query.message, is_callback=True)

    @dp.message_handler(commands=["buy"])
    async def show_purchase_command(message: types.Message):
        await send_purchase_screen(message)

async def send_purchase_screen(target, is_callback=False):
    text = (
        "💎 <b>Начни свой диалог</b>\n\n"
        "WorldTalk — это живой разговор с цифровыми персонажами.\n"
        "Общение доступно со всеми — без ограничений.\n\n"
        "💡 <b>Для общения используются голоса:</b>\n"
        "1 голос = 1 ответ персонажа\n\n"
        "⚙️ <b>Как это работает?</b>\n"
        "• Выбери нужное количество голосов\n"
        "• Общайся с любыми персонажами\n"
        "• Голоса действуют 60 дней с момента покупки\n\n"
        "💼 <b>Выбери свой тариф:</b>\n\n"
        "🕯️ <b>Lite</b> — 100 голосов — <b>149₽</b>\n"
        "💠 <b>Pro</b> — 250 голосов — <b>249₽</b>\n"
        "♾ <b>Ultra</b> — 500 голосов — <b>379₽</b>\n\n"
        "Выбери тариф 👇🏻"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🕯️ Lite", callback_data="lite_payment"),
        types.InlineKeyboardButton("💠 Pro", callback_data="pro_payment")
    )
    keyboard.add(types.InlineKeyboardButton("♾ Ultra", callback_data="ultra_payment"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))

    if is_callback:
        await target.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.reply(text, reply_markup=keyboard, parse_mode="HTML")