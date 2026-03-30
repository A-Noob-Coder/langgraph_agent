# src/db/models/user.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.db.base import Base

class User(Base):
    """系统用户实体表"""
    __tablename__ = "users"

    # 使用 UUID 作为底层系统主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 用户身份交互名
    username = Column(String(50), unique=True, index=True, nullable=False)
    
    # Bcrypt 死串
    hashed_password = Column(String(255), nullable=False)
    
    # 生命周期标志
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
