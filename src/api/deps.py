# src/api/deps.py
from fastapi import Depends, Header, HTTPException, Request, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.core.security import decode_access_token

# 这里的 tokenUrl 指向我们即将创建的登录网关
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """从 JWT 提取 user_id。拦截未经授权的访问。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return user_id

def get_session_id(
    x_session_id: str = Header(None, alias="X-Session-ID"),
    session_id: str = Query(None),
) -> str:
    session_id = session_id or x_session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    return session_id

def get_checkpointer_dep(request: Request) -> AsyncPostgresSaver:
    """从 app.state 获取复用的 checkpointer 实例（lifespan 中初始化）。"""
    return request.app.state.checkpointer
