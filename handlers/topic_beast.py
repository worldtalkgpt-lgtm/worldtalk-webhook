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

CHARACTER_NAME = "мистер бист"
searcher = FAISSSearcher(
    index_path=FAISS_CONFIG[CHARACTER_NAME]["index_path"],
    mapping_path=FAISS_CONFIG[CHARACTER_NAME]["mapping_path"]
)

async def show_beast_topics(callback_query: types.CallbackQuery):
    await callback_query.answer()

    # ✅ Клавиатура с темами
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        types.InlineKeyboardButton("🎦 Путь на YouTube", callback_data="beast_topic_Путь на YouTube"),
        types.InlineKeyboardButton("💸 Деньги и Бизнес", callback_data="beast_topic_Деньги бизнес и влияние")
    )
    keyboard.row(
        types.InlineKeyboardButton("💡 Контент и Идеи", callback_data="beast_topic_Контент и идеи")
    )
    keyboard.row(
        types.InlineKeyboardButton("📈 Рост и Будущее", callback_data="beast_topic_Масштаб и будущее"),
        types.InlineKeyboardButton("👼 Детство", callback_data="beast_topic_Детство")
    )
    keyboard.row(
        types.InlineKeyboardButton("🤝 Друзья и Команда", callback_data="beast_topic_Дружба в моей жизни")
    )

    # 🔙 Назад
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

    text = (
        "<b>┌ ✅ Фейсконтроль пройден ┐</b>\n"
        "|\n"
        "Доступ открыт.\n"
        "Перед тобой — диалог с легендой.\n"
        "|\n"
        "<b>└ 💰 Выбери тему для разговора ┘</b>"
    )

    await callback_query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def handle_topic_selected(callback_query: types.CallbackQuery):
    await callback_query.answer()
    topic = callback_query.data.replace("beast_topic_", "").strip()
    async with get_session() as session:
        user = await get_or_create_user(session, callback_query.from_user.id)
        await reset_other_character_topics(session, user.id, CHARACTER_NAME)
        await set_character_topic(session, user.id, CHARACTER_NAME, topic)

    # ✅ Просто сообщение о выбранной теме
    await callback_query.message.answer(
        f"🟢 Ты выбрал тему: <b>{topic}</b>\n<i>Давай начнём разговор...</i>",
        parse_mode="HTML"
    )

def setup(dp: Dispatcher):
    dp.register_callback_query_handler(show_beast_topics, lambda c: c.data == "beast_correct")
    dp.register_callback_query_handler(handle_topic_selected, lambda c: c.data.startswith("beast_topic_"))