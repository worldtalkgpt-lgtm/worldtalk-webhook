from openai import OpenAI
import numpy as np
from config import OPENAI_API_KEY, EMBEDDING_MODEL_NAME

class EmbeddingGenerator:
    def __init__(self):
        # Создаём клиент один раз
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Получает эмбеддинг текста через OpenAI API (новый интерфейс)
        :param text: входной текст пользователя
        :return: numpy-вектор
        """
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL_NAME,
                input=[text]
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            print(f"❌ Ошибка генерации эмбеддинга: {e}")
            # Возвращаем вектор той же размерности, что модель
            return np.zeros((3072,), dtype=np.float32)