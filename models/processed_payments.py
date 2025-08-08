from sqlalchemy import Column, String, Integer, DateTime, func
from db.base import Base

class ProcessedPayment(Base):
    __tablename__ = "processed_payments"

    transaction_id = Column(String, primary_key=True)  # уникальный ID из CloudPayments
    account_id     = Column(String, nullable=True)     # telegram_id из AccountId
    amount         = Column(Integer, nullable=True)    # сумма в копейках (опционально)
    created_at     = Column(DateTime, server_default=func.now())
