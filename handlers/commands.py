from aiogram.dispatcher import Dispatcher
from handlers.menu import setup as setup_menu
from handlers.purchase import setup as setup_purchase
from handlers.referral import setup as setup_referral

def register_commands(dp: Dispatcher):
    setup_menu(dp)
    setup_purchase(dp)
    setup_referral(dp)
