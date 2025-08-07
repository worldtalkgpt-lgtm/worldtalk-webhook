import json

# Путь к твоему mapping-файлу
mapping_path = "/root/worldtalk/beast/beast_mapping.json"

# Какой персонаж нас интересует
expected_character = "мистер бист"

with open(mapping_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Фильтруем только по персонажу, без темы
results = [
    item for item in data
    if item.get("character", "").strip().lower() == expected_character
]

print(f"🔎 Найдено {len(results)} фраз для персонажа '{expected_character}':\n")

for r in results:
    print(f"ID: {r.get('id')} | text: {r.get('text')} | audio_path: {r.get('audio_path')}")
