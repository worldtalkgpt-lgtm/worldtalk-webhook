import random
import numpy as np
import logging
import re
from utils.faiss_searcher import FAISSSearcher
from db.user_repo import (
    get_or_create_user,
    get_or_create_character_state,
    get_character_used_ids,
    add_character_used_id,
    get_character_dialog_position,
    increment_character_dialog_position,
    get_character_last_question_id,
    set_character_last_question_id,
    has_character_received_greeting,
    mark_character_greeting_sent,
    get_character_topic,
    get_character_subtopic,
    get_character_next_question_interval,
    set_character_next_question_interval,
    set_character_subtopic,
    decrement_user_voice_by_internal_id
)

logger = logging.getLogger(__name__)

class DialogManager:
    def __init__(self, searcher: FAISSSearcher, character_name: str):
        self.character = character_name.lower().strip()
        self.searcher = searcher
        self.min_q_interval = 4
        self.max_q_interval = 7

        self.character_phrases = [
            p for p in self.searcher.mapping
            if str(p.get("character", "")).lower().strip() == self.character
        ]
        self.phrase_by_id = {str(p["id"]): p for p in self.character_phrases}
        logger.info(f"[{self.character}] Загружено {len(self.character_phrases)} фраз.")

    async def get_next_phrase(self, session, telegram_id: int, embedding: np.ndarray):
        user = await get_or_create_user(session, telegram_id)
        user_id = user.id

        await get_or_create_character_state(session, user_id, self.character)
        topic = await get_character_topic(session, user_id, self.character)
        if not topic:
            logger.error(f"[{self.character}] Нет темы для пользователя {telegram_id}")
            return None

        subtopic = await get_character_subtopic(session, user_id, self.character)

        if not await has_character_received_greeting(session, user_id, self.character, topic):
            await mark_character_greeting_sent(session, user_id, self.character, topic)
            greeting = self._pick_random_greeting(topic, subtopic)
            if greeting:
                await self._update_state(session, user_id, greeting)  # ⬅️ Voice списывается!
                return greeting

        used_ids = await get_character_used_ids(session, user_id, self.character)
        candidates = self._filter_candidates(topic, subtopic, used_ids)
        if not candidates:
            logger.warning(f"[{self.character}] Сброс used_ids для темы '{topic}'")
            candidates = self._filter_candidates(topic, subtopic, set())

        dialog_pos = await get_character_dialog_position(session, user_id, self.character)
        last_q_id = await get_character_last_question_id(session, user_id, self.character)

        if last_q_id:
            return await self._handle_question_response(session, user_id, embedding, candidates)

        if await self._is_question_time(session, user_id, dialog_pos):
            q = await self._handle_question(session, user_id, embedding, candidates)
            if q:
                return q

        return await self._handle_main_phrase(session, user_id, embedding, candidates)

    async def _handle_question_response(self, session, user_id, embedding, candidates):
        reactions = [p for p in candidates if p.get("layer") in ["reaction", "follow_up"]]
        if not reactions:
            reactions = candidates
        best = self._pick_best_by_embedding(embedding, reactions)
        await set_character_last_question_id(session, user_id, self.character, None)
        await self._update_state(session, user_id, best)
        return best

    async def _is_question_time(self, session, user_id, dialog_pos):
        if dialog_pos == 0:
            return False
        q_interval = await get_character_next_question_interval(session, user_id, self.character)
        if not q_interval:
            q_interval = random.randint(self.min_q_interval, self.max_q_interval)
            await set_character_next_question_interval(session, user_id, self.character, q_interval)
        return dialog_pos % q_interval == 0

    async def _handle_question(self, session, user_id, embedding, candidates):
        questions = [p for p in candidates if p.get("layer") == "question"]
        if not questions:
            return None
        q = self._pick_best_by_embedding(embedding, questions)
        await set_character_last_question_id(session, user_id, self.character, int(q["id"]))
        new_interval = random.randint(self.min_q_interval, self.max_q_interval)
        await set_character_next_question_interval(session, user_id, self.character, new_interval)
        await self._update_state(session, user_id, q)
        return q

    async def _handle_main_phrase(self, session, user_id, embedding, candidates):
        mains = [p for p in candidates if p.get("layer") == "main"]
        if not mains:
            mains = candidates
        best = self._pick_best_by_embedding(embedding, mains)
        await self._update_state(session, user_id, best)
        return best

    def _filter_candidates(self, topic, subtopic, used_ids):
        return [
            p for p in self.character_phrases
            if p.get("topic") == topic
            and (not subtopic or p.get("subtopic") == subtopic)
            and str(p.get("id")) not in used_ids
        ]

    def _pick_random_greeting(self, topic, subtopic):
        greetings = [
            p for p in self.character_phrases
            if p.get("topic") == topic
            and (not subtopic or p.get("subtopic") == subtopic)
            and p.get("layer") == "main"
        ]
        return random.choice(greetings) if greetings else None

    def _pick_best_by_embedding(self, embedding, phrases):
        if not phrases:
            return None
        if len(phrases) <= 3:
            return random.choice(phrases)
        candidate_ids = [p["id"] for p in phrases]
        result = self.searcher.search_with_filter(embedding, candidate_ids)
        best_id = result["id"] if result else None
        return self.phrase_by_id.get(str(best_id)) or random.choice(phrases)

    async def _update_state(self, session, user_id, phrase, skip_voice: bool = False):
        await add_character_used_id(session, user_id, self.character, phrase["id"])
        await increment_character_dialog_position(session, user_id, self.character)
        if not skip_voice:
            await decrement_user_voice_by_internal_id(session, user_id)
        if "subtopic_trigger" in phrase and phrase["subtopic_trigger"]:
            await set_character_subtopic(session, user_id, self.character, phrase["subtopic_trigger"])