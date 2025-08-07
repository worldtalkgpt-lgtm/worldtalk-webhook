from aiogram import types
from aiogram.dispatcher import Dispatcher
from handlers.topic_arni import show_arni_topics
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
    mark_facecheck_passed
)
from utils.faiss_searcher import FAISSSearcher
from config import FAISS_CONFIG
import os, random

MAX_INVITES_PER_WEEK = 5
CHARACTER_NAME = "arni"

searcher = FAISSSearcher(
    index_path=FAISS_CONFIG[CHARACTER_NAME]["index_path"],
    mapping_path=FAISS_CONFIG[CHARACTER_NAME]["mapping_path"]
)

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "arnold")
    async def process_facecheck_arnold(callback_query: types.CallbackQuery):
        telegram_id = callback_query.from_user.id
        async with get_session() as session:
            user = await get_or_create_user(session, telegram_id)
            if await has_passed_facecheck(session, user.id, CHARACTER_NAME):
                await callback_query.answer()
                await show_arni_topics(callback_query)
                return

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("4️⃣", callback_data="arnold_wrong_4"),
            types.InlineKeyboardButton("6️⃣", callback_data="arnold_wrong_6"),
        )
        keyboard.add(
            types.InlineKeyboardButton("7️⃣", callback_data="arnold_correct"),
            types.InlineKeyboardButton("8️⃣", callback_data="arnold_wrong_8"),
        )
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

        text = (
            "<b>┌ 🧠 Фейсконтроль ┐</b>\n\n"
            "Ты стоишь на пороге диалога с человеком‑эпохой.\n"
            "Его сила стала символом целой эры.\n\n"
            "❓ <b>Сколько раз Арни побеждал на соревнованиях Mr. Olympia?</b>"
        )

        await callback_query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    @dp.callback_query_handler(lambda c: c.data == "arnold_correct")
    async def correct_answer(callback_query: types.CallbackQuery):
        telegram_id = callback_query.from_user.id
        await callback_query.message.edit_text(
            "<b>✅ Абсолютно верно. 7 титулов.</b>\n\n"
            "7 раз он доказал, что невозможное — это ничто.\n\n"
            "🔓 Доступ открыт. Добро пожаловать!",
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
                            print(f"[🦾 Арни 🦾] Ошибка при отправке сообщения: {e}")

        # 👋 Приветствие Арни + списание голоса
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

        await show_arni_topics(callback_query)

    @dp.callback_query_handler(lambda c: c.data.startswith("arnold_wrong"))
    async def wrong_answer(callback_query: types.CallbackQuery):
        wrong_messages = {
            "arnold_wrong_4": "❌ Он бы не остановился на четырёх. Попробуй снова!",
            "arnold_wrong_6": "❌ Шесть — почти, но не легендарная семёрка. Попробуй ещё раз!",
            "arnold_wrong_8": "❌ Восемь? Он был велик, но титулов ровно семь. Попробуй ещё раз!"
        }
        msg = wrong_messages.get(callback_query.data, "❌ Неверный ответ. Попробуй ещё раз.")

        retry_keyboard = types.InlineKeyboardMarkup(row_width=1)
        retry_keyboard.add(types.InlineKeyboardButton("🔁 Попробовать ещё раз", callback_data="arnold"))
        retry_keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="select_character"))

        await callback_query.message.edit_text(
            msg,
            parse_mode="HTML",
            reply_markup=retry_keyboard
        )