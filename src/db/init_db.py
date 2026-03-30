# src/db/init_db.py
from sqlalchemy import text
from src.db.session import engine

async def init_db() -> None:
    async with engine.begin() as conn:
        # 示例：用户表（实际项目用 ORM 模型 + migration）
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
            """)
        )
