from aiogram import types
from aiogram.dispatcher import Dispatcher
import os
import random

from handlers.topic_beast import show_beast_topics
from db.session import get_session
from db.user_repo import (
    get_or_create_user,
    get_referrer_id,
    get_user_by_internal_id,
    get_invited_this_week,
    increment_invited_this_week,
    add_voices,
    spend_voice,
    InsufficientVoicesError,
    has_passed_facecheck,
    mark_facecheck_passed,
)
from utils.faiss_searcher import FAISSSearcher
from config import FAISS_CONFIG

CHARACTER_NAME = "мистер бист"
MAX_INVITES_PER_WEEK = 5

searcher = FAISSSearcher(
    index_path=FAISS_CONFIG[CHARACTER_NAME]["index_path"],
    mapping_path=FAISS_CONFIG[CHARACTER_NAME]["mapping_path"]
)

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "beast")
    async def process_facecheck_beast(callback_query: types.CallbackQuery):
        telegram_id = callback_query.from_user.id
        async with get_session() as session:
            user = await get_or_create_user(session, telegram_id)
            if await has_passed_facecheck(session, user.id, CHARACTER_NAME):
                await callback_query.answer()
                await show_beast_topics(callback_query)
                return

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("311 млн", callback_data="beast_wrong_311"),
            types.InlineKeyboardButton("500 млн", callback_data="beast_wrong_500"),
        )
        keyboard.add(
            types.InlineKeyboardButton("400+ млн", callback_data="beast_correct"),
            types.InlineKeyboardButton("900 млн", callback_data="beast_wrong_900"),
        )
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

        text = (
            "<b>┌ 🧠 Фейсконтроль ┐</b>\n\n"
            "Он — символ новой эры YouTube.\n"
            "Покажи, что ты знаком с его достижениями.\n\n"
            "❓ <b>Сколько подписчиков у Мистера Биста на YouTube?</b>"
        )

        await callback_query.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    @dp.callback_query_handler(lambda c: c.data == "beast_correct")
    async def correct_answer(callback_query: types.CallbackQuery):
        telegram_id = callback_query.from_user.id
        await callback_query.message.edit_text(
            "<b>✅ Верно. 400+ млн.</b>\n\nДобро пожаловать в диалог с королём контента!",
            parse_mode="HTML"
        )

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
                            print(f"[💰 Мистер B💰] Ошибка при отправке сообщения: {e}")

        # 👋 Приветствие с оплатой голосом
        greetings = [
            p for p in searcher.mapping
            if p.get("layer") == "main"
            and p.get("topic") == "Приветствие"
            and str(p.get("character", "")).lower() == CHARACTER_NAME
        ]
        if greetings:
            g = random.choice(greetings)
            audio_path = g.get("audio_path")

            async with get_session() as session:
                try:
                    await spend_voice(session, telegram_id)
                except InsufficientVoicesError:
                    await callback_query.message.answer("❌ У тебя закончились голоса. Пополни счёт, чтобы продолжить.")
                    return

            if audio_path and os.path.exists(audio_path):
                with open(audio_path, "rb") as v:
                    await callback_query.message.answer_voice(voice=v, caption=g.get("text", "👋 Привет!"))
            else:
                await callback_query.message.answer(g.get("text", "👋 Привет!"))

        await show_beast_topics(callback_query)

    @dp.callback_query_handler(lambda c: c.data.startswith("beast_wrong"))
    async def wrong_answer(callback_query: types.CallbackQuery):
        wrong_messages = {
            "beast_wrong_311": "❌ Уже давно не 311 млн! Попробуй снова.",
            "beast_wrong_500": "❌ Нет, он ещё не дошёл до 500 млн.",
            "beast_wrong_900": "❌ Это слишком. Даже для него.",
        }
        msg = wrong_messages.get(callback_query.data, "❌ Неверный ответ.")
        retry_keyboard = types.InlineKeyboardMarkup(row_width=1)
        retry_keyboard.add(types.InlineKeyboardButton("🔁 Попробовать ещё раз", callback_data="beast"))
        retry_keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

        await callback_query.message.edit_text(msg, reply_markup=retry_keyboard, parse_mode="HTML")