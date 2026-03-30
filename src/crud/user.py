# src/crud/user.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.models.user import User
from src.core.security import get_password_hash

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """通过 username 从库中精准捞取用户"""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, username: str, plain_password: str) -> User:
    """注册用户：对密码 Hash 保护后存入实体库"""
    hashed_password = get_password_hash(plain_password)
    new_user = User(
        username=username,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
