from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.base import Base

class UserCharacterState(Base):
    __tablename__ = "user_character_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_name = Column(String, nullable=False)

    topic = Column(String, nullable=True)
    used_ids = Column(String, nullable=True)
    dialog_position = Column(Integer, default=0)
    last_question_id = Column(Integer, nullable=True)
    current_subtopic = Column(String, nullable=True)
    greetings_sent = Column(String, nullable=True)

    # 🔥 если нужно управлять интервалом вопросов
    next_question_interval = Column(Integer, nullable=True)

    # ⭐ Новое поле: пройден ли фейсконтроль для этого персонажа
    facecheck_passed = Column(Boolean, default=False)

    user = relationship("User", backref="character_states")