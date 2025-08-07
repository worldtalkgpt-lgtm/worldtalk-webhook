from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    voices = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 📌 Реферальная система
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)

    # 📌 Подписка
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    total_spent = Column(Integer, default=0)

    # 📌 Безопасность и аналитика
    last_active = Column(DateTime, default=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)
    language = Column(String, default="en")

    # 📌 Диалоговая логика
    topic = Column(String, nullable=True)
    subtopic = Column(String, nullable=True)  # 🔥 добавляем поддержку подтем
    used_ids = Column(String, default="")
    dialog_position = Column(Integer, default=0)
    last_question_id = Column(String, nullable=True)
    greetings_sent = Column(String, default="")
    invited_this_week = Column(Integer, default=0)
    last_message = Column(String, nullable=True)

    # 📌 Правильные связи
    referrer = relationship("User", remote_side=[id])

    rewards_given = relationship(
        "ReferralReward",
        back_populates="referrer",
        foreign_keys="ReferralReward.referrer_id"
    )
