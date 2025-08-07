import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ✅ Загружаем переменные окружения из .env
load_dotenv()

# ================================
# 🔑 ОСНОВНЫЕ ПЕРЕМЕННЫЕ
# ================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# 🔑 Ключ OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ Внимание: OPENAI_API_KEY не найден в .env. Проверь настройки!")

# 🔑 URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не задан в .env!")

# ================================
# 🔥 НАСТРОЙКИ FAISS ДЛЯ ВСЕХ ПЕРСОНАЖЕЙ
# ================================
FAISS_CONFIG = {
    "месси": {
        "index_path": "/home/worldtalk_admin/worldtalk/messi/faiss_index_messi.index",
        "mapping_path": "/home/worldtalk_admin/worldtalk/messi/messi_mapping.json",
        "audio_dir": "/home/worldtalk_admin/worldtalk/audio_cache"
    },
    "мистер бист": {
        "index_path": "/home/worldtalk_admin/worldtalk/beast/faiss_index_beast.index",
        "mapping_path": "/home/worldtalk_admin/worldtalk/beast/beast_mapping.json",
        "audio_dir": "/home/worldtalk_admin/worldtalk/beast/beast_audio"
    },
    "arni": {
        "index_path": "/home/worldtalk_admin/worldtalk/arni/faiss_index_arni.index",
        "mapping_path": "/home/worldtalk_admin/worldtalk/arni/arni_mapping.json",
        "audio_dir": "/home/worldtalk_admin/worldtalk/arni/arni_audio"
    }
}

# ================================
# 🧠 НАСТРОЙКИ ЭМБЕДДИНГОВ
# ================================
EMBEDDING_DIMENSION = 3072
EMBEDDING_MODEL_NAME = "text-embedding-3-large"

# ================================
# 🗄️ НАСТРОЙКА БАЗЫ ДАННЫХ
# ================================
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Логировать SQL-запросы
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# ================================
# ✅ ПРОВЕРКА КОНФИГУРАЦИИ
# ================================
def check_config() -> bool:
    """Проверяет корректность конфигурации и наличие всех необходимых файлов"""
    errors = []

    # Проверка токена
    if not BOT_TOKEN or len(BOT_TOKEN) < 10:
        errors.append("❌ BOT_TOKEN не задан или некорректен")

    # Проверка ключа OpenAI
    if not OPENAI_API_KEY:
        errors.append("❌ OPENAI_API_KEY не задан или некорректен")

    # Проверка FAISS файлов и аудиодиректорий
    for character, paths in FAISS_CONFIG.items():
        index_path = paths.get("index_path")
        mapping_path = paths.get("mapping_path")
        audio_dir = paths.get("audio_dir")

        if not index_path or not os.path.exists(index_path):
            errors.append(f"❌ index_path не найден для {character}: {index_path}")
        if not mapping_path or not os.path.exists(mapping_path):
            errors.append(f"❌ mapping_path не найден для {character}: {mapping_path}")
        if not audio_dir or not os.path.exists(audio_dir):
            errors.append(f"❌ Аудиодиректория не найдена для {character}: {audio_dir}")

    # Проверка размерности эмбеддингов
    if EMBEDDING_DIMENSION != 3072:
        errors.append(f"❌ Размерность эмбеддингов должна быть 3072, установлена: {EMBEDDING_DIMENSION}")

    # Итог
    if errors:
        print("\n".join(errors))
        return False

    print("✅ Конфигурация успешно проверена")
    return True

# 🚀 Автопроверка при запуске напрямую
if __name__ == "__main__":
    check_config()
