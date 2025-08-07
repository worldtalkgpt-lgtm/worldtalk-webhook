from aiogram import types, Dispatcher
import os, random

AUDIO_DIR = "/root/worldtalk/beast/beast_audio"

async def cmd_testbeast(message: types.Message):
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
    if not files:
        await message.answer("⚠️ Нет файлов в AUDIO_DIR")
        return
    file = random.choice(files)
    with open(os.path.join(AUDIO_DIR, file), "rb") as voice:
        await message.answer_voice(voice)

def setup(dp: Dispatcher):
    dp.register_message_handler(cmd_testbeast, commands=["testbeast"], state="*")
