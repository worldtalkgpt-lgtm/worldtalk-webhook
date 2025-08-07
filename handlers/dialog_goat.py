import logging
import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.session import AsyncSessionLocal
from db.user_repo import get_or_create_user, get_character_topic, get_user_voices
from utils.faiss_searcher import FAISSSearcher
from utils.dialog_manager import DialogManager
from utils.embedding_generator import EmbeddingGenerator
from config import FAISS_CONFIG

logger = logging.getLogger(__name__)

CHARACTER_NAME = "месси"
goat_manager: DialogManager | None = None

# 🚦 Глобальный лок для пользователей
processing_users = set()

async def init_goat_manager():
    global goat_manager
    if goat_manager is None:
        conf = FAISS_CONFIG[CHARACTER_NAME]
        searcher = FAISSSearcher(conf["index_path"], conf["mapping_path"])
        goat_manager = DialogManager(searcher, CHARACTER_NAME)
        logger.info("✅ Диалоговый менеджер для 🇦🇷 G.O.A.T🐐 инициализирован")

async def is_goat(message: types.Message) -> bool:
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id)
        topic = await get_character_topic(session, user.id, CHARACTER_NAME)
        return topic is not None

async def handle_start_goat(message: types.Message):
    await message.answer("🐐 Вы начали диалог с 🇦🇷 G.O.A.T🐐!\nНапишите сообщение.")

async def handle_goat_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # ✅ Проверяем лок
    if user_id in processing_users:
        await message.answer("⏳ Подожди, я ещё думаю над предыдущим сообщением…")
        return

    processing_users.add(user_id)
    try:
        if goat_manager is None:
            await init_goat_manager()

        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(session, user_id)
            voices_left = await get_user_voices(session, user_id)
            if voices_left <= 0:
                keyboard = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("💎 Купить голоса", callback_data="buy")
                )
                await message.answer(
                    "💔 У вас закончились голоса.\n"
                    "Чтобы продолжить общение, купите дополнительный пакет голосов.",
                    reply_markup=keyboard
                )
                return

            topic = await get_character_topic(session, user.id, CHARACTER_NAME)
            if not topic:
                return

            embedding = EmbeddingGenerator().get_embedding(message.text)
            phrase = await goat_manager.get_next_phrase(session, user_id, embedding)
            if phrase:
                audio_path = phrase.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    with open(audio_path, "rb") as audio:
                        await message.answer_voice(voice=audio, caption=phrase.get("text", ""))
                else:
                    await message.answer(phrase.get("text", ""))
            else:
                await message.answer("🐐 К сожалению, я пока не готов ответить.")
    except Exception as e:
        logger.error(f"[🇦🇷 G.O.A.T🐐] Ошибка: {e}", exc_info=True)
        await message.answer("Произошла ошибка, попробуйте снова.")
    finally:
        processing_users.discard(user_id)

def setup(dp):
    dp.register_message_handler(handle_start_goat, commands=["messi"], state="*")
    dp.register_message_handler(handle_goat_message, is_goat, content_types=types.ContentTypes.TEXT, state="*")
