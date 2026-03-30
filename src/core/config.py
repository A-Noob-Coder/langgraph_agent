# src/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)


class Settings(BaseSettings):
    """项目配置类"""
    
    # Database
    DATABASE_URL: str = Field(None, description="异步数据库连接字符串 (SQLAlchemy)")
    LANGGRAPH_DATABASE_URL: str = Field(None, description="同步数据库连接字符串")
    
    # LLM
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str = "https://api.siliconflow.cn/v1"
    MODEL_NAME: str = "Qwen/Qwen3-8B"
    TEMPERATURE: float = 0.7
    
    # Tools
    TAVILY_API_KEY: str | None = None
    
    # Memory
    MAX_CONTEXT_TOKENS: int = 20000   # 消息窗口最大 token 数，超出后自动截断旧消息
    
    # Security
    SECRET_KEY: str = "insecure-secret-key"
    
    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # 忽略未定义的环境变量

# 全局单例配置对象
settings = Settings()

# 简单测试配置是否加载成功
if __name__ == "__main__":
    print("环境变量加载。。。")
    print(f"Model: {settings.MODEL_NAME}")
    print(f"Database URL: {settings.DATABASE_URL}")
