import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher

from db.session import get_session
from db.user_repo import (
    register_user_with_referrer,
    get_user_by_id,
    set_user_topic
)

# 🎯 Логгер
logger = logging.getLogger(__name__)

def setup(dp: Dispatcher):
    @dp.message_handler(commands=["start"])
    async def handle_start(message: types.Message):
        telegram_id = message.from_user.id
        logger.info(f"🚀 /start вызван пользователем {telegram_id}")

        referrer_id = None

        # ✅ Проверяем аргументы для реферала
        args = message.get_args()
        if args and args.startswith("ref_"):
            try:
                ref_telegram_id = int(args.split("_")[1])
                if ref_telegram_id != telegram_id:
                    async with get_session() as session:
                        ref_user = await get_user_by_id(session, ref_telegram_id)
                        if ref_user:
                            referrer_id = ref_user.id
                        else:
                            logger.warning(f"⚠️ Реферер {ref_telegram_id} не найден в БД")
            except Exception as e:
                logger.error(f"⚠️ Ошибка обработки реферального аргумента: {e}")

        # ✅ Работаем с базой
        try:
            async with get_session() as session:
                user = await get_user_by_id(session, telegram_id)
                if user is None:
                    await register_user_with_referrer(session, telegram_id, referrer_id)
                    await set_user_topic(session, telegram_id, None)
                    await session.commit()
                    logger.info(f"✅ Новый пользователь {telegram_id} создан")
                else:
                    logger.info(f"ℹ️ Пользователь {telegram_id} уже зарегистрирован")
        except Exception as e:
            logger.error(f"❌ Ошибка при работе с базой: {e}")

        # ✅ Клавиатура
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text="🌟 Персонажи", callback_data="select_character")
        )
        keyboard.add(
            InlineKeyboardButton(text="👤 Профиль", callback_data="menu"),
            InlineKeyboardButton(text="💎 Купить голоса", callback_data="buy")
        )

        # ✅ Финальный текст приветствия со смайлами и чистой структурой
        welcome_text = (
            "🌍 <b>Добро пожаловать в WorldTalk!</b>\n\n"
            "🇦🇷 Лионель Месси — эмоции футбола\n"
            "🦍 Арнольд Шварценеггер — сила и мотивация\n"
            "🎥 MrBeast — энергия миллиардов зрителей\n\n"
            "📍 <b>WorldTalk</b> — это творческий медиапроект.\n"
            "Фразы заранее записаны и основаны на цитатах из открытых источников.\n"
            "Бот не является официальным лицом этих людей.\n\n"
            "✨ Вы получаете 10 голосов бесплатно\n"
            "🗣 1 голос = 1 фраза от легенды\n\n"
            "⬇️ Нажмите «Персонажи» и начните диалог"
        )

        try:
            await message.answer(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.info(f"✅ Приветственное сообщение отправлено пользователю {telegram_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке приветствия пользователю {telegram_id}: {e}")