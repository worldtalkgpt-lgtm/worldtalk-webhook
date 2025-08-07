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

CHARACTER_NAME = "arni"
arni_manager: DialogManager | None = None

# 🚦 Глобальный лок для пользователей (Arni)
processing_users_arni = set()

async def init_arni_manager():
    global arni_manager
    if arni_manager is None:
        conf = FAISS_CONFIG[CHARACTER_NAME]
        searcher = FAISSSearcher(conf["index_path"], conf["mapping_path"])
        arni_manager = DialogManager(searcher, CHARACTER_NAME)
        logger.info("✅ Диалоговый менеджер для 🦾Арни🦾 инициализирован")

async def is_arni(message: types.Message) -> bool:
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id)
        topic = await get_character_topic(session, user.id, CHARACTER_NAME)
        return topic is not None

async def handle_start_arni(message: types.Message):
    await message.answer("🦾 Ты начал диалог с 🦾Железным Арни!\nНапиши ему что‑нибудь.")

async def handle_arni_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # ✅ Проверяем лок
    if user_id in processing_users_arni:
        await message.answer("⏳ Подожди, я ещё думаю над предыдущим сообщением…")
        return

    processing_users_arni.add(user_id)
    try:
        if arni_manager is None:
            await init_arni_manager()

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
            phrase = await arni_manager.get_next_phrase(session, user_id, embedding)
            if phrase:
                audio_path = phrase.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    with open(audio_path, "rb") as audio:
                        await message.answer_voice(voice=audio, caption=phrase.get("text", ""))
                else:
                    await message.answer(phrase.get("text", ""))
            else:
                await message.answer("🦾 К сожалению, я пока не готов ответить.")
    except Exception as e:
        logger.error(f"[🦾Арни🦾] Ошибка: {e}", exc_info=True)
        await message.answer("Произошла ошибка, попробуйте снова.")
    finally:
        processing_users_arni.discard(user_id)

def setup(dp):
    dp.register_message_handler(handle_start_arni, commands=["arni"], state="*")
    dp.register_message_handler(handle_arni_message, is_arni, content_types=types.ContentTypes.TEXT, state="*")
