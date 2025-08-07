import faiss
import json
import numpy as np
import os
import re
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI


class FAISSSearcher:
    def __init__(self, index_path: str, mapping_path: str, openai_api_key: Optional[str] = None):
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"❌ FAISS индекс не найден: {index_path}")
        if not os.path.exists(mapping_path):
            raise FileNotFoundError(f"❌ Mapping JSON не найден: {mapping_path}")

        self.index = faiss.read_index(index_path)

        with open(mapping_path, "r", encoding="utf-8") as f:
            self.mapping: List[Dict[str, Any]] = json.load(f)

        self.mapping_by_id = {item["id"]: item for item in self.mapping if "id" in item}

        if len(self.mapping) != self.index.ntotal:
            raise ValueError(
                f"⚠️ Несоответствие размеров: mapping({len(self.mapping)}) и index({self.index.ntotal})"
            )

        self.openai = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None

        print(f"✅ FAISS загружен: {index_path}, фраз: {len(self.mapping)}")

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        used_ids: Optional[set] = None,
        topic: Optional[str] = None,
        subtopic: Optional[str] = None,
        character: Optional[str] = None,
        emotion: Optional[str] = None,
        layer: Optional[str] = None,
        user_input: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(query_embedding, axis=0).astype("float32")

        distances, indices = self.index.search(query_embedding, k * 5)
        result: List[Dict[str, Any]] = []

        user_words = set(re.findall(r'\w+', user_input.lower())) if user_input else set()

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.mapping):
                continue

            item = self.mapping[idx]

            if topic and item.get("topic", "").strip().lower() != topic.strip().lower():
                continue
            if subtopic and item.get("subtopic", "").strip().lower() != subtopic.strip().lower():
                continue
            if character and item.get("character", "").strip().lower() != character.strip().lower():
                continue
            if emotion and item.get("emotion", "").strip().lower() != emotion.strip().lower():
                continue
            if layer and item.get("layer", "").strip().lower() != layer.strip().lower():
                continue
            if used_ids and str(item.get("id")) in used_ids:
                continue

            text_words = set(re.findall(r'\w+', item.get("text", "").lower()))
            word_overlap = len(user_words & text_words)
            hybrid_score = -dist + 0.2 * word_overlap

            result.append({
                **item,
                "embedding_score": float(-dist),
                "word_score": word_overlap,
                "hybrid_score": hybrid_score
            })

        result.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return result[:k]

    async def search_with_reranking(
        self,
        query_embedding: np.ndarray,
        user_input: str,
        k: int = 5,
        **filters
    ) -> Dict[str, Any]:
        candidates = self.search(query_embedding, k=k * 2, user_input=user_input, **filters)
        if not self.openai or len(candidates) <= 1:
            return candidates[0] if candidates else {}

        options = "\n".join([f"{i+1}. {c['text']}" for i, c in enumerate(candidates)])
        prompt = (
            f"Пользователь сказал: \"{user_input}\"\n"
            f"Выбери самый подходящий ответ из списка ниже.\n"
            f"{options}\n"
            f"Ответь только числом от 1 до {len(candidates)}."
        )

        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            choice = int(response.choices[0].message.content.strip())
            return candidates[choice - 1]
        except Exception as e:
            print(f"⚠️ Ошибка в reranking: {e}")
            return candidates[0] if candidates else {}

    def search_with_filter(self, embedding: np.ndarray, allowed_ids: List[int]) -> Optional[Dict[str, Any]]:
        if embedding.ndim == 1:
            embedding = np.expand_dims(embedding, axis=0).astype("float32")

        distances, indices = self.index.search(embedding, len(self.mapping))

        best_id = None
        best_score = float("inf")

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.mapping):
                continue
            item = self.mapping[idx]
            item_id = item.get("id")
            if item_id in allowed_ids:
                if dist < best_score:
                    best_score = dist
                    best_id = item_id

        return {"id": best_id, "score": -best_score} if best_id is not None else None