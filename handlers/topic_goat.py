from aiogram import types
from aiogram.dispatcher import Dispatcher
import logging

from db.session import get_session
from utils.faiss_searcher import FAISSSearcher
from db.user_repo import (
    get_or_create_user,
    set_character_topic,
    reset_other_character_topics
)
from config import FAISS_CONFIG

logger = logging.getLogger(__name__)

CHARACTER_NAME = "месси"
searcher = FAISSSearcher(
    index_path=FAISS_CONFIG[CHARACTER_NAME]["index_path"],
    mapping_path=FAISS_CONFIG[CHARACTER_NAME]["mapping_path"]
)

# 🔥 Этот хендлер только показывает список тем
async def show_goat_topics(callback_query: types.CallbackQuery):
    await callback_query.answer()

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🏟️ Барселона", callback_data="goat_topic_Барселона"),
        types.InlineKeyboardButton("🇫🇷 ПСЖ", callback_data="goat_topic_ПСЖ"),
    )
    keyboard.row(
        types.InlineKeyboardButton("🇦🇷 Сборная Аргентины", callback_data="goat_topic_Сборная Аргентины"),
    )
    keyboard.row(
        types.InlineKeyboardButton("🏆 ЧМ 2022", callback_data="goat_topic_Чемпионат мира 2022"),
        types.InlineKeyboardButton("👨‍👩‍👧‍👦 Семья", callback_data="goat_topic_Семья"),
    )
    keyboard.row(
        types.InlineKeyboardButton("⚔️ Месси vs Роналду", callback_data="goat_topic_Месси vs Роналду"),
    )

    # 🔙 Назад
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

    text = (
        "┌ ✅ Фейсконтроль пройден ┐\n\n\n"
        "Доступ открыт.  \n"
        "Перед тобой — диалог с легендой.  \n\n\n"
        "└ 🇦🇷 Выбери тему для разговора ┘"
    )

    await callback_query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

# 🔥 Этот хендлер только сохраняет выбранную тему (приветствие мы убрали отсюда)
async def handle_topic_selected(callback_query: types.CallbackQuery):
    await callback_query.answer()
    topic = callback_query.data.replace("goat_topic_", "").strip()
    async with get_session() as session:
        user = await get_or_create_user(session, callback_query.from_user.id)
        await reset_other_character_topics(session, user.id, CHARACTER_NAME)
        await set_character_topic(session, user.id, CHARACTER_NAME, topic)

        await callback_query.message.answer(
            f"🟢 Ты выбрал тему: <b>{topic}</b>\n<i>Давай начнём разговор...</i>",
            parse_mode="HTML"
        )

def setup(dp: Dispatcher):
    dp.register_callback_query_handler(show_goat_topics, lambda c: c.data == "messi_correct")
    dp.register_callback_query_handler(handle_topic_selected, lambda c: c.data.startswith("goat_topic_"))
