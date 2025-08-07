from typing import Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from models.user import User
from models.referral_reward import ReferralReward
from models.user_character_state import UserCharacterState

# ================================
# 🔧 Получить или создать пользователя
# ================================
async def get_or_create_user(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            telegram_id=user_id,
            voices=10,
            used_ids="",
            dialog_position=0,
            last_question_id=None,
            greetings_sent="",
            referrer_id=None,
            invited_this_week=0,
            last_message=None,
            subtopic=None
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

# ================================
# 📌 Получить пользователя по Telegram ID
# ================================
async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    return result.scalar_one_or_none()

# ✅ Получить пользователя по внутреннему ID
async def get_user_by_internal_id(session: AsyncSession, internal_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == internal_id))
    return result.scalar_one_or_none()

# ================================
# 🔧 Реферальная логика
# ================================
async def register_user_with_referrer(session: AsyncSession, user_id: int, referrer_id: Optional[int] = None):
    existing_user = await get_user_by_id(session, user_id)
    if existing_user:
        return
    user = User(
        telegram_id=user_id,
        voices=10,
        used_ids="",
        dialog_position=0,
        last_question_id=None,
        greetings_sent="",
        referrer_id=referrer_id,
        invited_this_week=0,
        last_message=None,
        subtopic=None
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_referrer_id(session: AsyncSession, user_id: int) -> Optional[int]:
    user = await get_user_by_id(session, user_id)
    return user.referrer_id if user else None

async def has_received_referral_bonus(session: AsyncSession, referrer_id: int, invited_user_id: int) -> bool:
    result = await session.execute(
        select(ReferralReward).where(
            ReferralReward.referrer_id == referrer_id,
            ReferralReward.invited_id == invited_user_id
        )
    )
    return result.scalar_one_or_none() is not None

async def mark_referral_bonus_given(session: AsyncSession, referrer_id: int, invited_user_id: int):
    reward = ReferralReward(referrer_id=referrer_id, invited_id=invited_user_id)
    session.add(reward)
    await session.commit()

async def get_invited_this_week(session: AsyncSession, user_id: int) -> int:
    user = await get_user_by_id(session, user_id)
    return user.invited_this_week if user else 0

async def increment_invited_this_week(session: AsyncSession, user_id: int):
    user = await get_or_create_user(session, user_id)
    user.invited_this_week += 1
    await session.commit()

async def reset_weekly_invited(session: AsyncSession):
    await session.execute(update(User).values(invited_this_week=0))
    await session.commit()

# ================================
# 📌 Темы
# ================================
async def get_user_topic(session: AsyncSession, user_id: int) -> Optional[str]:
    user = await get_user_by_id(session, user_id)
    return user.topic if user else None

async def set_user_topic(session: AsyncSession, user_id: int, topic: Optional[str]):
    user = await get_or_create_user(session, user_id)
    user.topic = topic
    await session.commit()

# ================================
# 📌 Подтемы
# ================================
async def get_user_subtopic(session: AsyncSession, user_id: int) -> Optional[str]:
    user = await get_user_by_id(session, user_id)
    return user.subtopic if user else None

async def set_user_subtopic(session: AsyncSession, user_id: int, subtopic: Optional[str]):
    user = await get_or_create_user(session, user_id)
    user.subtopic = subtopic
    await session.commit()

# ================================
# 🎙 Голоса
# ================================
async def get_user_voices(session: AsyncSession, user_id: int) -> int:
    user = await get_user_by_id(session, user_id)
    return user.voices if user else 0

async def decrement_user_voice(session: AsyncSession, user_id: int):
    user = await get_user_by_id(session, user_id)
    if user and user.voices > 0:
        user.voices -= 1
        await session.commit()

async def decrement_user_voice_by_internal_id(session: AsyncSession, internal_id: int):
    user = await get_user_by_internal_id(session, internal_id)
    if user and user.voices > 0:
        user.voices -= 1
        await session.commit()

async def add_voices(session: AsyncSession, user_id: int, amount: int):
    await session.execute(
        update(User)
        .where(User.telegram_id == user_id)
        .values(voices=User.voices + amount)
    )
    await session.commit()

# ================================
# 📌 Использованные ID
# ================================
async def get_user_used_ids(session: AsyncSession, user_id: int) -> Set[str]:
    user = await get_user_by_id(session, user_id)
    return set(user.used_ids.split(",")) if user and user.used_ids else set()

async def add_user_used_id(session: AsyncSession, user_id: int, phrase_id: str):
    user = await get_or_create_user(session, user_id)
    ids = set(user.used_ids.split(",")) if user.used_ids else set()
    ids.add(str(phrase_id))
    user.used_ids = ",".join(sorted(ids))
    await session.commit()

# ================================
# 📌 Позиция диалога
# ================================
async def get_user_dialog_position(session: AsyncSession, user_id: int) -> int:
    user = await get_user_by_id(session, user_id)
    return user.dialog_position if user else 0

async def increment_user_dialog_position(session: AsyncSession, user_id: int):
    user = await get_or_create_user(session, user_id)
    user.dialog_position += 1
    await session.commit()

# ================================
# ❓ Последний вопрос
# ================================
async def get_last_question_id(session: AsyncSession, user_id: int) -> Optional[str]:
    user = await get_user_by_id(session, user_id)
    return user.last_question_id if user else None

async def set_last_question_id(session: AsyncSession, user_id: int, question_id: str):
    user = await get_or_create_user(session, user_id)
    user.last_question_id = question_id
    await session.commit()

# ================================
# 👋 Приветствия
# ================================
async def has_received_greeting(session: AsyncSession, user_id: int, topic: str) -> bool:
    user = await get_user_by_id(session, user_id)
    if not user or not user.greetings_sent:
        return False
    return topic in user.greetings_sent.split(",")

async def mark_greeting_sent(session: AsyncSession, user_id: int, topic: str):
    user = await get_or_create_user(session, user_id)
    topics = set(user.greetings_sent.split(",")) if user.greetings_sent else set()
    topics.add(topic)
    user.greetings_sent = ",".join(sorted(topics))
    await session.commit()

# ================================
# 💬 Последнее сообщение
# ================================
async def set_last_user_message(session: AsyncSession, user_id: int, message: str):
    user = await get_or_create_user(session, user_id)
    user.last_message = message
    await session.commit()

async def get_last_user_message(session: AsyncSession, user_id: int) -> Optional[str]:
    user = await get_user_by_id(session, user_id)
    return user.last_message if user else None

# ================================
# 🔥 Логика по состоянию персонажей
# ================================
async def get_or_create_character_state(session: AsyncSession, user_id: int, character_name: str) -> UserCharacterState:
    result = await session.execute(
        select(UserCharacterState).where(
            UserCharacterState.user_id == user_id,
            UserCharacterState.character_name == character_name
        )
    )
    state = result.scalar_one_or_none()
    if not state:
        state = UserCharacterState(
            user_id=user_id,
            character_name=character_name,
            used_ids="",
            dialog_position=0,
            last_question_id=None,
            greetings_sent="",
            current_subtopic=None,
            next_question_interval=None,
            facecheck_passed=False
        )
        session.add(state)
        await session.commit()
        await session.refresh(state)
    return state

async def get_character_topic(session: AsyncSession, user_id: int, character_name: str) -> Optional[str]:
    state = await get_or_create_character_state(session, user_id, character_name)
    return state.topic

async def set_character_topic(session: AsyncSession, user_id: int, character_name: str, topic: Optional[str]):
    state = await get_or_create_character_state(session, user_id, character_name)
    state.topic = topic
    await session.commit()

async def get_character_used_ids(session: AsyncSession, user_id: int, character_name: str) -> Set[str]:
    state = await get_or_create_character_state(session, user_id, character_name)
    return set(state.used_ids.split(",")) if state.used_ids else set()

async def add_character_used_id(session: AsyncSession, user_id: int, character_name: str, phrase_id: str):
    state = await get_or_create_character_state(session, user_id, character_name)
    ids = set(state.used_ids.split(",")) if state.used_ids else set()
    ids.add(str(phrase_id))
    state.used_ids = ",".join(sorted(ids))
    await session.commit()

async def get_character_dialog_position(session: AsyncSession, user_id: int, character_name: str) -> int:
    state = await get_or_create_character_state(session, user_id, character_name)
    return state.dialog_position

async def increment_character_dialog_position(session: AsyncSession, user_id: int, character_name: str):
    state = await get_or_create_character_state(session, user_id, character_name)
    state.dialog_position += 1
    await session.commit()

async def get_character_last_question_id(session: AsyncSession, user_id: int, character_name: str) -> Optional[str]:
    state = await get_or_create_character_state(session, user_id, character_name)
    return state.last_question_id

async def set_character_last_question_id(session: AsyncSession, user_id: int, character_name: str, question_id: str):
    state = await get_or_create_character_state(session, user_id, character_name)
    state.last_question_id = question_id
    await session.commit()

async def get_character_subtopic(session: AsyncSession, user_id: int, character_name: str) -> Optional[str]:
    state = await get_or_create_character_state(session, user_id, character_name)
    return state.current_subtopic

async def set_character_subtopic(session: AsyncSession, user_id: int, character_name: str, subtopic: Optional[str]):
    state = await get_or_create_character_state(session, user_id, character_name)
    state.current_subtopic = subtopic
    await session.commit()

async def has_character_received_greeting(session: AsyncSession, user_id: int, character_name: str, topic: str) -> bool:
    state = await get_or_create_character_state(session, user_id, character_name)
    if not state or not state.greetings_sent:
        return False
    return topic in state.greetings_sent.split(",")

async def mark_character_greeting_sent(session: AsyncSession, user_id: int, character_name: str, topic: str):
    state = await get_or_create_character_state(session, user_id, character_name)
    topics = set(state.greetings_sent.split(",")) if state.greetings_sent else set()
    topics.add(topic)
    state.greetings_sent = ",".join(sorted(topics))
    await session.commit()

async def get_character_next_question_interval(session: AsyncSession, user_id: int, character_name: str) -> Optional[int]:
    state = await get_or_create_character_state(session, user_id, character_name)
    return state.next_question_interval

async def set_character_next_question_interval(session: AsyncSession, user_id: int, character_name: str, interval: int):
    state = await get_or_create_character_state(session, user_id, character_name)
    state.next_question_interval = interval
    await session.commit()

# ⭐ Facecheck
async def has_passed_facecheck(session: AsyncSession, user_id: int, character_name: str) -> bool:
    state = await get_or_create_character_state(session, user_id, character_name)
    return bool(getattr(state, "facecheck_passed", False))

async def mark_facecheck_passed(session: AsyncSession, user_id: int, character_name: str):
    state = await get_or_create_character_state(session, user_id, character_name)
    state.facecheck_passed = True
    await session.commit()

# ================================
# 📌 Сброс других персонажей
# ================================
async def reset_other_character_topics(session: AsyncSession, user_id: int, current_character: str):
    result = await session.execute(
        select(UserCharacterState).where(UserCharacterState.user_id == user_id)
    )
    states = result.scalars().all()
    for state in states:
        if state.character_name != current_character:
            state.topic = None
            state.current_subtopic = None
            state.used_ids = ""
            state.dialog_position = 0
            state.last_question_id = None
            state.greetings_sent = ""
            state.next_question_interval = None
    await session.commit()

# ================================
# 📌 Списание голоса (унифицированное)
# ================================
class InsufficientVoicesError(Exception):
    pass

async def spend_voice(session: AsyncSession, user_id: int):
    user = await get_user_by_id(session, user_id)
    if not user or user.voices <= 0:
        raise InsufficientVoicesError("Not enough voices")
    user.voices -= 1
    await session.commit()