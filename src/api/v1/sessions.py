# src/api/v1/sessions.py
"""对话（session）管理接口。"""
from fastapi import APIRouter, Depends
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.api.deps import get_current_user, get_checkpointer_dep
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/sessions")
async def list_sessions(
    user_id: str = Depends(get_current_user),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer_dep),
):
    """查询当前用户的所有会话列表。

    原理：thread_id 格式为 "{user_id}:{session_id}"，
    遍历 checkpointer 中所有 checkpoint，过滤出属于当前用户的 thread。
    """
    sessions = []
    seen_threads = set()

    try:
        # alist 遍历所有 checkpoint 元数据
        async for checkpoint_tuple in checkpointer.alist({}):
            config = checkpoint_tuple.config
            thread_id = config.get("configurable", {}).get("thread_id", "")

            # 仅返回属于当前用户的 session（thread_id 以 user_id: 开头）
            if not thread_id.startswith(f"{user_id}:"):
                continue

            # 去重（同一 thread 可能有多个 checkpoint）
            if thread_id in seen_threads:
                continue
            seen_threads.add(thread_id)

            # 提取 session_id（去掉 user_id: 前缀）
            session_id = thread_id[len(user_id) + 1:]

            # 提取最后一条消息的摘要（用于列表展示）
            checkpoint_data = checkpoint_tuple.checkpoint
            messages = checkpoint_data.get("channel_values", {}).get("messages", [])
            last_message_preview = ""
            if messages:
                last_msg = messages[-1]
                content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
                last_message_preview = content[:100] if isinstance(content, str) else ""

            sessions.append({
                "session_id": session_id,
                "thread_id": thread_id,
                "message_count": len(messages),
                "last_message_preview": last_message_preview,
            })

    except Exception as e:
        logger.error("Error listing sessions: %s", e, exc_info=True)
        # 部分数据可能已收集，仍然返回
        pass

    logger.info("Listed %d sessions for user=%s", len(sessions), user_id)
    return {"user_id": user_id, "sessions": sessions, "total": len(sessions)}
