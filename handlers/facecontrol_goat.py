from aiogram import types
from aiogram.dispatcher import Dispatcher
from handlers.topic_goat import show_goat_topics
from db.session import get_session
from db.user_repo import (
    get_or_create_user,
    get_referrer_id,
    get_user_by_internal_id,
    get_invited_this_week,
    increment_invited_this_week,
    add_voices,
    has_passed_facecheck,
    mark_facecheck_passed,
    spend_voice,
    InsufficientVoicesError,
    mark_character_greeting_sent
)
import os
import random
from utils.faiss_searcher import FAISSSearcher
from config import FAISS_CONFIG

CHARACTER_NAME = "месси"
MAX_INVITES_PER_WEEK = 5

# Заранее загружаем приветственные фразы
searcher = FAISSSearcher(
    index_path=FAISS_CONFIG[CHARACTER_NAME]["index_path"],
    mapping_path=FAISS_CONFIG[CHARACTER_NAME]["mapping_path"]
)
greetings = [
    p for p in searcher.mapping
    if p.get("layer") == "main"
    and p.get("topic") == "Приветствие"
    and str(p.get("character", "")).lower() == CHARACTER_NAME
]

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "messi")
    async def process_facecheck_messi(callback_query: types.CallbackQuery):
        telegram_id = callback_query.from_user.id
        async with get_session() as session:
            user = await get_or_create_user(session, telegram_id)
            if await has_passed_facecheck(session, user.id, CHARACTER_NAME):
                await callback_query.answer()
                await show_goat_topics(callback_query)
                return

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.row(
            types.InlineKeyboardButton("2014", callback_data="messi_wrong_2014"),
            types.InlineKeyboardButton("2018", callback_data="messi_wrong_2018")
        )
        keyboard.row(
            types.InlineKeyboardButton("2022", callback_data="messi_correct"),
            types.InlineKeyboardButton("Никогда не становился", callback_data="messi_wrong_never")
        )
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

        text = (
            "<b>┌ 🧠 Фейсконтроль ┐</b>\n\n"
            "Ты на пороге диалога с легендой футбола.\n"
            "Докажи, что достоин услышать его голос!\n\n"
            "❓ <b>В каком году Месси стал чемпионом мира?</b>"
        )
        await callback_query.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data == "messi_correct")
    async def correct_answer(callback_query: types.CallbackQuery):
        telegram_id = callback_query.from_user.id
        async with get_session() as session:
            user = await get_or_create_user(session, telegram_id)
            await mark_facecheck_passed(session, user.id, CHARACTER_NAME)

            referrer_internal_id = await get_referrer_id(session, telegram_id)
            if referrer_internal_id:
                ref_user = await get_user_by_internal_id(session, referrer_internal_id)
                if ref_user:
                    invited = await get_invited_this_week(session, ref_user.telegram_id)
                    if invited < MAX_INVITES_PER_WEEK:
                        await add_voices(session, ref_user.telegram_id, 20)
                        await increment_invited_this_week(session, ref_user.telegram_id)
                        try:
                            await callback_query.bot.send_message(
                                ref_user.telegram_id,
                                "🎉 Твой друг прошёл фейсконтроль!\n\n+20 голосов начислено 🙌"
                            )
                        except Exception as e:
                            print(f"[G.O.A.T] Ошибка при отправке сообщения рефереру: {e}")

        await callback_query.message.edit_text(
            "<b>✅ Легендарный момент!</b>\n\n"
            "Ты прошёл фейсконтроль G.O.A.T.\n"
            "🎧 Готовься… Он сам приветствует тебя 👇",
            parse_mode="HTML"
        )

        if greetings:
            async with get_session() as session:
                try:
                    await spend_voice(session, telegram_id)
                except InsufficientVoicesError:
                    await callback_query.message.answer("❌ У тебя закончились голоса. Пополни счёт, чтобы продолжить.")
                    return

                # Помечаем greeting как отправленный (важно!)
                await mark_character_greeting_sent(session, user.id, CHARACTER_NAME, topic="Приветствие")

            g = random.choice(greetings)
            audio_path = g.get("audio_path")
            if audio_path and os.path.exists(audio_path):
                with open(audio_path, "rb") as v:
                    await callback_query.message.answer_voice(voice=v, caption=g.get("text", "👋 Привет!"))
            else:
                await callback_query.message.answer(g.get("text", "👋 Привет!"))

        await show_goat_topics(callback_query)

    @dp.callback_query_handler(lambda c: c.data.startswith("messi_wrong"))
    async def wrong_answer(callback_query: types.CallbackQuery):
        wrong_messages = {
            "messi_wrong_2014": "❌ Почти! В 2014 он был близок, но не стал чемпионом.",
            "messi_wrong_2018": "❌ 2018 год? Нет, это не его триумф.",
            "messi_wrong_never": "❌ Ошибочка. Он стал чемпионом, и весь мир это помнит!",
        }
        msg = wrong_messages.get(callback_query.data, "❌ Неверный ответ.")
        retry_keyboard = types.InlineKeyboardMarkup(row_width=1)
        retry_keyboard.add(types.InlineKeyboardButton("🔁 Попробовать ещё раз", callback_data="messi"))
        retry_keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))
        await callback_query.message.edit_text(msg, reply_markup=retry_keyboard, parse_mode="HTML")