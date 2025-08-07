from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote

from db.session import get_session
from db.user_repo import get_invited_this_week

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "referral")
    async def referral_callback(callback_query: types.CallbackQuery):
        await send_referral(callback_query.from_user.id, callback_query.message, is_callback=True)

    @dp.message_handler(commands=["referral"])
    async def referral_command(message: types.Message):
        await send_referral(message.from_user.id, message)


async def send_referral(user_id, target, is_callback=False):
    invite_link = f"https://t.me/WorldTalkBot?start=ref_{user_id}"
    share_text = f"🎯 Присоединяйся к WorldTalk и получи голос легенды!\n\n@WorldTalkBot {invite_link}"
    encoded_text = quote(share_text)
    share_url = f"https://t.me/share/url?url={encoded_text}"

    async with get_session() as session:
        invited = await get_invited_this_week(session, user_id)
        voices_earned = invited * 20
        remaining = max(0, 5 - invited)

    # ✨ Обновлённый текст с линией после блока максимум
    text = (
        "<b>┌ 🎯 1 друг = +20 голосов ┐</b>\n"
        "\n"
        "🍀Пригласи друзей в WorldTalk.\n"
        "Как только они пройдут фейсконтроль.\n"
        "Ты получишь + 20 голосов!\n\n\n"
        "📊Твои результаты:\n"
        f"• Приглашено: <b>{invited}</b>\n"
        f"• Голосов получено: <b>{voices_earned}</b>\n"
        f"• Осталось в лимите: <b>{remaining}</b>\n"
        "<b>└ 📩 Поделиться ┘</b>"
    )

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📤 Поделиться ссылкой", url=share_url),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )

    if is_callback:
        await target.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.reply(text, parse_mode="HTML", reply_markup=markup)