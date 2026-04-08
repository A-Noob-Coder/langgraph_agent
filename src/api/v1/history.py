# src/api/v1/history.py
from fastapi import APIRouter, Depends, HTTPException, Query
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.api.deps import get_current_user, get_session_id, get_checkpointer_dep
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _build_thread_id(user_id: str, session_id: str) -> str:
    """统一的 thread_id 构造，绑定 user_id 以实现用户隔离。"""
    return f"{user_id}:{session_id}"


@router.get("/history")
async def get_history(
    user_id: str = Depends(get_current_user),
    session_id: str = Depends(get_session_id),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer_dep),
):
    """获取指定会话的历史记录。"""
    config = {
        "configurable": {
            "thread_id": _build_thread_id(user_id, session_id)
        }
    }

    try:
        checkpoint_tuple = await checkpointer.aget_tuple(config)

        if not checkpoint_tuple:
            return {"summary": "", "messages": []}

        checkpoint_data = checkpoint_tuple.checkpoint
        messages = checkpoint_data.get("channel_values", {}).get("messages", [])
        # 获取底层隐性保留的长期记忆摘要
        summary = checkpoint_data.get("channel_values", {}).get("summary", "")

        # 兼容不同 LangGraph 版本
        if not messages and "messages" in checkpoint_data:
            messages = checkpoint_data["messages"]
        if not summary and "summary" in checkpoint_data:
            summary = checkpoint_data["summary"]

        serialized_messages = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                serialized_messages.append(msg.model_dump())
            elif hasattr(msg, "dict"):
                serialized_messages.append(msg.dict())
            else:
                serialized_messages.append(str(msg))

        return {"summary": summary, "messages": serialized_messages}

    except Exception as e:
        logger.error("Error fetching history: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.delete("/history")
async def clear_history(
    user_id: str = Depends(get_current_user),
    session_id: str = Depends(get_session_id),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer_dep),
):
    """清除指定会话的历史记录。"""
    config = {
        "configurable": {
            "thread_id": _build_thread_id(user_id, session_id)
        }
    }

    try:
        # TODO: 实现实际的清理逻辑
        return {"detail": "History clear request accepted (implement logic as needed)"}

    except Exception as e:
        logger.error("Error clearing history: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clear history")
