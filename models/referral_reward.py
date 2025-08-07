from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.base import Base

class ReferralReward(Base):
    __tablename__ = "referral_rewards"  # ✅ обязательно с двумя подчёркиваниями

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # ✅ Уникальная пара (referrer_id + invited_id), чтобы не начислить дважды
    __table_args__ = (
        UniqueConstraint("referrer_id", "invited_id", name="unique_referral_pair"),
    )

    # ✅ Связи
    referrer = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="rewards_given"
    )
    invited = relationship(
        "User",
        foreign_keys=[invited_id]
    )
