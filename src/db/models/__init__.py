# src/db/models/__init__.py
"""暴露目前系统中所有的 ORM 实体，协助 Alembic 在 env.py 中的 base.metadata.create_all() 反射感知"""
from .user import User
