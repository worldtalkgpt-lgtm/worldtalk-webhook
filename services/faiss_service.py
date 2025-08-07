import faiss
import numpy as np
import json
import logging
from typing import List, Dict, Optional, Set

# 🔧 Логирование
logging.basicConfig(
    filename="faiss_searcher.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class FAISSSearcher:
    def __init__(self, index_path: str, mapping_path: str):
        """
        Загружает FAISS-индекс и mapping.
        :param index_path: путь к .index
        :param mapping_path: путь к .json с метаданными
        """
        logging.info(f"Загрузка FAISS-индекса: {index_path}")
        self.index = faiss.read_index(index_path)

        logging.info(f"Загрузка mapping: {mapping_path}")
        with open(mapping_path, "r", encoding="utf-8") as f:
            self.mapping: Dict[str, Dict] = json.load(f)

        # Проверим, сколько элементов в маппинге
        logging.info(f"Загружено {len(self.mapping)} элементов из mapping")

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        used_ids: Optional[Set[str]] = None,
        topic: Optional[str] = None
    ) -> List[Dict]:
        """
        Ищет ближайшие фразы по embedding и теме.
        """
        if used_ids is None:
            used_ids = set()

        # 💡 Нормализация эмбеддинга
        norm = np.linalg.norm(query_embedding)
        if norm == 0:
            logging.warning("‼ Нулевой эмбеддинг, возвращаем пустой список.")
            return []
        query_embedding = query_embedding / norm

        # 🔎 Поиск в FAISS
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            k * 3  # ищем с запасом
        )

        results: List[Dict] = []
        fallback: List[Dict] = []

        topic_lower = topic.strip().lower() if topic else None

        for idx in indices[0]:
            idx = int(idx)
            item = self.mapping.get(str(idx))
            if not item:
                logging.warning(f"[FAISS] Нет item в mapping по ключу {idx}")
                continue

            # Пропускаем уже использованные
            if str(item.get("id")) in used_ids:
                continue

            # Фильтр по теме
            if topic_lower:
                item_topic = str(item.get("topic", "")).strip().lower()
                if item_topic == topic_lower:
                    results.append(item)
                else:
                    fallback.append(item)
            else:
                results.append(item)

            if len(results) >= k:
                break

        # Если не нашли достаточно по теме — добавляем из fallback
        if topic_lower and len(results) < k:
            for item in fallback:
                if str(item.get("id")) in used_ids:
                    continue
                results.append(item)
                if len(results) >= k:
                    break

        logging.info(f"[FAISS] topic={topic_lower} → найдено {len(results)} кандидатов")
        return results[:k]
