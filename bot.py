import logging
from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from dotenv import load_dotenv
from config import BOT_TOKEN

# 👉 Базовые хендлеры
from handlers import (
    setup_start,
    setup_character,
    setup_menu,
    setup_referral,
    setup_purchase
)

# 💰 Экраны покупки по тарифам
from handlers.purchase_lite import setup as setup_purchase_lite
from handlers.purchase_pro import setup as setup_purchase_pro
from handlers.purchase_ultra import setup as setup_purchase_ultra

# 🔒 Фейсконтроль
from handlers.facecontrol_goat import setup as setup_fc_goat
from handlers.facecheck_beast import setup as setup_fc_beast
from handlers.facecheck_arnold import setup as setup_fc_arnold

# 📌 Темы
from handlers.topic_goat import setup as setup_topic_goat
from handlers.topic_beast import setup as setup_topic_beast
from handlers.topic_arni import setup as setup_topic_arni

# 🎙 Диалоги
from handlers.dialog_goat import setup as setup_dialog_goat
from handlers.dialog_beast import setup as setup_dialog_beast
from handlers.dialog_arni import setup as setup_dialog_arni

# 📖 Подробнее о боте
from handlers.about_bot import setup as setup_about_bot

# =====================================
# 🔧 Базовая настройка
# =====================================
load_dotenv()
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# 🚦 Подключаем защиту от спама
from middlewares.rate_limit import RateLimitMiddleware
dp.middleware.setup(RateLimitMiddleware(limit_per_sec=1.0))

# 🛡️ Глобальный обработчик ошибок
@dp.errors_handler()
async def global_error_handler(update, exception):
    logging.error(f"⚠️ Error: {exception}")
    return True

# 📋 Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)  # ✅ Финальный фикс: name

# =====================================
# 📌 Регистрируем хендлеры
# =====================================
setup_start(dp)
setup_character(dp)
setup_menu(dp)
setup_referral(dp)
setup_purchase(dp)

setup_purchase_lite(dp)
setup_purchase_pro(dp)
setup_purchase_ultra(dp)

setup_fc_goat(dp)
setup_fc_beast(dp)
setup_fc_arnold(dp)

setup_topic_goat(dp)
setup_topic_beast(dp)
setup_topic_arni(dp)

setup_dialog_goat(dp)
setup_dialog_beast(dp)
setup_dialog_arni(dp)

setup_about_bot(dp)

# =====================================
# ▶️ Стартовое действие
# =====================================
async def on_startup(_):
    logger.info("✅ Бот запущен и готов к бою!")

if __name__ == "__main__":  # ✅ Финально правильно
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)