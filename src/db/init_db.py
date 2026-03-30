# src/db/init_db.py
from src.core.logger import get_logger

logger = get_logger(__name__)

async def init_db() -> None:
    """
    预留位置。
    表结构的自动化构建已交由 Alembic migration 控制。
    这里可放置日后系统必须的初始业务数据埋点 (例如初始 admin 账号创建)。
    """
    logger.info("init_db checkpoint reached. Table schema creation is managed by Alembic.")
