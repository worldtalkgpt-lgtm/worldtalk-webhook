import faiss
import json
import numpy as np
from openai import OpenAI
import os

# Загрузка индекса
index_path = "/root/worldtalk/messi/faiss_index_messi.index"
mapping_path = "/root/worldtalk/messi/messi_mapping.json"

index = faiss.read_index(index_path)

with open(mapping_path, "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Функция для получения эмбеддинга с помощью OpenAI
def get_embedding(text: str) -> np.ndarray:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Embedding.create(
        model="text-embedding-3-large",
        input=[text]
    )
    embedding = np.array(response["data"][0]["embedding"], dtype=np.float32)
    return embedding.reshape(1, -1)

# Главная функция — получает лучший ответ по входному тексту
def get_best_phrase(user_input: str) -> str:
    embedding = get_embedding(user_input)
    _, I = index.search(embedding, 1)
    best_id = str(I[0][0])
    return mapping.get(best_id, "Фраза не найдена.")
