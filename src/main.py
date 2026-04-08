# src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import auth, chat, history, sessions
from src.db.init_db import init_db
from src.agent.memory import get_checkpointer
from src.agent import graph as agent_graph
from src.core.logger import get_logger
from src.core.exception_handlers import register_exception_handlers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("🚀 Starting up...")

    # 1. 初始化业务数据库表
    await init_db()
    logger.info("✅ Business database initialized.")

    # 2. 使用上下文管理器管理 checkpointer 的生命周期
    async with get_checkpointer() as checkpointer:
        # 编译 Agent Graph
        agent_graph.graph = agent_graph.build_agent_graph(checkpointer)
        logger.info("✅ Agent Graph compiled with AsyncPostgresSaver.")

        # 将 checkpointer 存入 app.state，供 API 层复用
        app.state.checkpointer = checkpointer

        yield  # 应用运行中

    # 关闭时
    logger.info("🛑 Application shutdown complete.")

app = FastAPI(
    title="LangGraph Agent",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "streamlit://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(history.router, prefix="/api/v1", tags=["history"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])


@app.get("/health")
async def health():
    return {"status": "ok"}
