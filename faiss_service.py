import faiss
import json
import numpy as np

class FAISSService:
    def __init__(self, index_path: str, mapping_path: str):
        self.index = faiss.read_index(index_path)
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)

    def search_all(self, embedding: list, top_k: int = 5):
        query = np.array([embedding]).astype('float32')
        distances, indices = self.index.search(query, top_k)
        results = []
        for idx in indices[0]:
            if str(idx) in self.mapping:
                results.append(self.mapping[str(idx)])
        return results

    def search_by_topic(self, embedding: list, topic: str, top_k: int = 5):
        query = np.array([embedding]).astype('float32')
        distances, indices = self.index.search(query, len(self.mapping))  # ищем среди всех
        results = []
        for idx in indices[0]:
            item = self.mapping.get(str(idx))
            if item and item.get("topic") == topic:
                results.append(item)
                if len(results) >= top_k:
                    break
        return results
