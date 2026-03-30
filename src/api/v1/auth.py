# src/api/v1/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.core.security import verify_password, create_access_token
from src.core.config import settings
from src.db.session import get_db
from src.crud.user import get_user_by_username, create_user

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register_new_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """真实业务：创建用户并写入实体库"""
    user = await get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该用户名已被注册",
        )
    user = await create_user(db, username=user_in.username, plain_password=user_in.password)
    return {"message": "User created successfully", "user_id": str(user.id)}

@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """真实业务：去数据库校验用户信息并下发 JWT Token"""
    
    # 1.拿着 form_data.username 到刚才写好的 crud 去查 SQLAlchemy
    user_record = await get_user_by_username(db, username=form_data.username)
    
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 2. 对比密码 Hash (使用原生 bcrypt 底层)
    if not verify_password(form_data.password, user_record.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 3. 生成 Token，剥离底层的 uuid 放入 sub (作为用户门票)
    user_id = str(user_record.id)
    access_token = create_access_token(
        subject=user_id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
