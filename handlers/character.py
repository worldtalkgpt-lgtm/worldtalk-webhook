from aiogram import types
from aiogram.dispatcher import Dispatcher

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "select_character")
    async def process_character_selection(callback_query: types.CallbackQuery):
        keyboard = types.InlineKeyboardMarkup(row_width=2)

        # ✅ Кнопки: Лионель Месси — один в ряду
        keyboard.row(
            types.InlineKeyboardButton("🇦🇷 Лионель Месси", callback_data="messi")
        )
        # ✅ Кнопки: MrBeast и Арнольд Шварценеггер во втором ряду
        keyboard.row(
            types.InlineKeyboardButton("🎥 MrBeast", callback_data="beast"),
            types.InlineKeyboardButton("🦍 Арнольд Шварценеггер", callback_data="arnold"),
        )
        # ✅ Кнопка «Назад» отдельной строкой
        keyboard.row(
            types.InlineKeyboardButton("🔙 Назад", callback_data="menu")
        )

        description = (
            "<b>🌟 Персонажи</b>\n"
            "Выбери легенду, с которой начнёшь диалог:\n\n"
            "🇦🇷 <b>Лионель Месси</b>\n"
            "8 «Золотых мячей» • Чемпион мира 2022\n"
            "Живые эмоции футбола\n\n"
            "🎥 <b>MrBeast</b>\n"
            "250+ млн подписчиков • Миллионы розданных $\n"
            "Энергия миллиардов зрителей\n\n"
            "🦍 <b>Арнольд Шварценеггер</b>\n"
            "7× «Мистер Олимпия» • Звезда «Терминатора»\n"
            "Сила и мотивация\n\n"
            "Кого выберешь? 🌎"
        )

        await callback_query.message.edit_text(
            description,
            reply_markup=keyboard,
            parse_mode="HTML"
        )