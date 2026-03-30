# src/api/deps.py
from fastapi import Header, HTTPException, Request
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def get_current_user(
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID")
    return x_user_id

def get_session_id(
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> str:
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-ID")
    return x_session_id

def get_checkpointer_dep(request: Request) -> AsyncPostgresSaver:
    """从 app.state 获取复用的 checkpointer 实例（lifespan 中初始化）。"""
    return request.app.state.checkpointer
