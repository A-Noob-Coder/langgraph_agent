# src/db/session.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 生命周期依赖：提供基于请求局部的数据库会话连接并在使用完毕后安全回收。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
