from aiogram import types
from aiogram.dispatcher import Dispatcher
from db.session import get_session
from db.user_repo import get_user_by_id

async def send_menu(user_id, target, is_callback=False):
    async with get_session() as session:
        user = await get_user_by_id(session, user_id)

    username = target.from_user.username or "неизвестно"
    voices = user.voices if user else 0

    menu_text = (
        "<b>┌ 📋 Профиль ┐</b>\n\n"
        f"Имя: @{username}\n"
        f"ID: {user_id}\n"
        f"Голоса: {voices}\n\n"
        "⚠️ Это не живой чат!\n"
        "Бот ищет реальные цитаты звёзд из открытых источников.\n"
        "Ответы могут не соответствовать контексту вашего «вопроса».\n\n"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🌟 Персонажи", callback_data="select_character"),
        types.InlineKeyboardButton("💎 Купить голоса", callback_data="buy"),
    )
    keyboard.add(
        types.InlineKeyboardButton("💬 Обратная связь", url="https://t.me/supWT"),
        types.InlineKeyboardButton("🎁 Пригласить друга", callback_data="referral")
    )
    keyboard.add(
        types.InlineKeyboardButton("ℹ️ О боте", callback_data="about_bot")
    )

    if is_callback:
        await target.edit_text(menu_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.reply(menu_text, reply_markup=keyboard, parse_mode="HTML")

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "menu")
    async def show_menu_callback(callback_query: types.CallbackQuery):
        await send_menu(callback_query.from_user.id, callback_query.message, is_callback=True)

    @dp.message_handler(commands=["menu"])
    async def show_menu_command(message: types.Message):
        await send_menu(message.from_user.id, message)