from .start import setup as setup_start
from .character import setup as setup_character
from .menu import setup as setup_menu
from .referral import setup as setup_referral
from .purchase import setup as setup_purchase

# 💰 Экраны покупки по тарифам
from .purchase_lite import setup as setup_purchase_lite
from .purchase_pro import setup as setup_purchase_pro
from .purchase_ultra import setup as setup_purchase_ultra

# 📖 Подробнее о боте
from .about_bot import setup as setup_about_bot

# ✅ Фейсконтроль
from .facecontrol_goat import setup as setup_fc_goat
from .facecheck_beast import setup as setup_fc_beast
from .facecheck_arnold import setup as setup_fc_arnold

# ✅ Темы
from .topic_goat import setup as setup_topic_goat
from .topic_beast import setup as setup_topic_beast
from .topic_arni import setup as setup_topic_arni

# ✅ Диалоги
from .dialog_goat import setup as setup_dialog_goat
from .dialog_beast import setup as setup_dialog_beast
from .dialog_arni import setup as setup_dialog_arni

# ✅ Тестовый (если нужен)
from .test_beast_voice import setup as setup_test_beast_voice

# ✅ Команды
from .commands import register_commands

def setup_all(dp):
    setup_start(dp)
    setup_character(dp)
    setup_menu(dp)
    setup_referral(dp)
    setup_purchase(dp)

    # 💰 Покупка
    setup_purchase_lite(dp)
    setup_purchase_pro(dp)
    setup_purchase_ultra(dp)

    # 🔒 Фейсконтроль
    setup_fc_goat(dp)
    setup_fc_beast(dp)
    setup_fc_arnold(dp)

    # 📌 Темы
    setup_topic_goat(dp)
    setup_topic_beast(dp)
    setup_topic_arni(dp)

    # 🎙 Диалоги
    setup_dialog_goat(dp)
    setup_dialog_beast(dp)
    setup_dialog_arni(dp)

    # 📖 О боте
    setup_about_bot(dp)

    # ✅ Команды и тест
    register_commands(dp)
    setup_test_beast_voice(dp)