from aiogram.dispatcher.middlewares import BaseMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable, Awaitable, Dict, Any


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_factory: sessionmaker):
        super().__init__()
        self.session_factory = session_factory

    async def on_pre_process_message(self, message, data: Dict[str, Any]):
        async with self.session_factory() as session:
            data["db"] = session


def get_db():
    from config import SessionLocal
    return SessionLocal
