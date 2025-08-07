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

CHARACTER_NAME = "arni"
searcher = FAISSSearcher(
    index_path=FAISS_CONFIG[CHARACTER_NAME]["index_path"],
    mapping_path=FAISS_CONFIG[CHARACTER_NAME]["mapping_path"]
)

# 📌 Отображение тем после фейсконтроля
async def show_arni_topics(callback_query: types.CallbackQuery):
    await callback_query.answer()

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    # первая строка
    keyboard.row(
        types.InlineKeyboardButton("🏋️‍♂️ Тренировки и тело", callback_data="arnold_topic_Тренировки и тело"),
        types.InlineKeyboardButton("🥇 Mr.Olimpia", callback_data="arnold_topic_Мистер Олимпия"),
    )
    # вторая строка
    keyboard.row(
        types.InlineKeyboardButton("🏛️ Политика и пост губернатора", callback_data="arnold_topic_Политика и пост губернатора"),
    )
    # третья строка
    keyboard.row(
        types.InlineKeyboardButton("🚀 Моё Начало", callback_data="arnold_topic_Моё начало"),
        types.InlineKeyboardButton("🎬 Голливуд", callback_data="arnold_topic_Голливуд"),
    )
    # четвёртая строка
    keyboard.row(
        types.InlineKeyboardButton("🤝 Поддержка и наставничество", callback_data="arnold_topic_Поддержка и наставничество"),
    )

    # кнопка назад
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

    text = (
        "<b>┌ ✅ Фейсконтроль пройден ┐</b>\n"
        "|\n"
        "Доступ открыт.\n"
        "Перед тобой — диалог с легендой.\n"
        "|\n"
        "<b>└ 🦾 Выбери тему для разговора ┘</b>"
    )

    await callback_query.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

# 📌 Обработка выбора темы
async def handle_topic_selected(callback_query: types.CallbackQuery):
    await callback_query.answer()
    topic = callback_query.data.replace("arnold_topic_", "").strip()
    async with get_session() as session:
        user = await get_or_create_user(session, callback_query.from_user.id)
        await reset_other_character_topics(session, user.id, CHARACTER_NAME)
        await set_character_topic(session, user.id, CHARACTER_NAME, topic)

        # Тут больше не отправляем приветствие — оно отправлено после фейсконтроля
        await callback_query.message.answer(
            f"🟢 Ты выбрал тему: <b>{topic}</b>\n<i>Давай начнём разговор...</i>",
            parse_mode="HTML"
        )

def setup(dp: Dispatcher):
    dp.register_callback_query_handler(show_arni_topics, lambda c: c.data == "arnold_correct")
    dp.register_callback_query_handler(handle_topic_selected, lambda c: c.data.startswith("arnold_topic_"))