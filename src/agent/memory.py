# src/agent/memory.py
from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def get_checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    """
    创建并管理 AsyncPostgresSaver 的生命周期。
    使用 from_conn_string 自动管理连接池。
    """
    logger.info("🔌 Initializing AsyncPostgresSaver...")

    async with AsyncPostgresSaver.from_conn_string(settings.LANGGRAPH_DATABASE_URL) as saver:
        await saver.setup()
        logger.info("✅ AsyncPostgresSaver initialized and tables created.")
        yield saver

    logger.info("✅ AsyncPostgresSaver connection closed.")
