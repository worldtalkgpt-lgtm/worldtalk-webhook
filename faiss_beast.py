import faiss
import json
import numpy as np
import os
from openai import OpenAI

# 📌 Пути к индексам и маппингу для Мистера Биста
index_path = "/root/worldtalk/beast/faiss_index_beast.index"
mapping_path = "/root/worldtalk/beast/beast_mapping.json"

# 📦 Загружаем индекс
index = faiss.read_index(index_path)

# 📖 Загружаем mapping
with open(mapping_path, "r", encoding="utf-8") as f:
    mapping = json.load(f)

# 🔑 OpenAI клиент
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ⚡ Функция для получения эмбеддинга
def get_embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    embedding = np.array(response.data[0].embedding, dtype=np.float32)
    return embedding.reshape(1, -1)

# 🚀 Основная функция — получить лучшую фразу
def best_phrase(user_input: str) -> str:
    embedding = get_embedding(user_input)
    distances, indices = index.search(embedding, 1)
    best_id = str(indices[0][0])
    return mapping.get(best_id, "Фраза не найдена.")
