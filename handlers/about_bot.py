from aiogram import types
from aiogram.dispatcher import Dispatcher
from handlers.menu import send_menu  # ✅ импортируем функцию меню

def setup(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == "about_bot")
    async def about_bot_handler(callback_query: types.CallbackQuery):
        about_text = (
            "<b>📖 Подробнее о WorldTalk</b>\n\n"
            "WorldTalk — это технологическая платформа нового поколения, "
            "которая открывает доступ к уникальному опыту общения с выдающимися личностями.\n\n"
            "Мы создаём пространство, где записи голосов и тщательно подобранные фразы "
            "превращаются в живой диалог. Вы выбираете персонажа, задаёте вопрос "
            "и получаете ответ в его настоящем голосе.\n\n"
            "WorldTalk разрабатывается как инструмент, объединяющий развлечение "
            "и глубокий интерес к людям, которые изменили мир. "
            "Это не игра и не случайный чат‑бот — это тщательно выстроенная система "
            "с продуманной экономикой и сценариями взаимодействия.\n\n"
            "Каждый ответ списывает единицу внутреннего ресурса — голос. "
            "Голоса можно пополнять и использовать в любое время, "
            "открывая всё больше диалогов и тем.\n\n"
            "Инфраструктура проекта построена на современных технологиях, "
            "обеспечивающих масштабируемость и стабильную работу.\n\n"
            "WorldTalk задуман как сервис, который даёт людям новый формат общения "
            "с теми, кого они никогда не смогут услышать лично. "
            "Это продукт для широкой аудитории и одновременно платформа."
        )

        # 🔘 Клавиатура с кнопкой назад
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="menu")
        )

        await callback_query.message.edit_text(
            about_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    # обработка "назад" уже есть в menu.py, но если хочешь, можем дополнительно
    # сделать тут, чтобы наверняка
    @dp.callback_query_handler(lambda c: c.data == "menu")
    async def back_to_menu(callback_query: types.CallbackQuery):
        await send_menu(callback_query.from_user.id, callback_query.message, is_callback=True)
