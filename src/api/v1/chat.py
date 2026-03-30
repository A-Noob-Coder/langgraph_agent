# src/api/v1/chat.py
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.agent import graph as agent_graph
from src.api.deps import get_current_user, get_session_id
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _build_thread_id(user_id: str, session_id: str) -> str:
    """统一的 thread_id 构造。"""
    return f"{user_id}:{session_id}"


@router.post("/chat")
async def chat(
    text: str,
    user_id: str = Depends(get_current_user),
    session_id: str = Depends(get_session_id),
):
    """非流式对话接口，等待完整响应后返回。"""
    if agent_graph.graph is None:
        raise RuntimeError("Graph not initialized. Check lifespan startup.")

    config = {
        "configurable": {
            "thread_id": _build_thread_id(user_id, session_id),
        }
    }
    state = {
        "user_id": user_id,
        "session_id": session_id,
        "messages": [HumanMessage(content=text)],
    }

    logger.info("Chat request: user=%s session=%s", user_id, session_id)
    result_state = await agent_graph.graph.ainvoke(state, config=config)
    last_message = result_state["messages"][-1]
    return {"content": last_message.content}


@router.post("/chat/stream")
async def chat_stream(
    text: str,
    user_id: str = Depends(get_current_user),
    session_id: str = Depends(get_session_id),
):
    """SSE 流式对话接口，逐块返回 LLM 输出。

    SSE 事件格式：
    - data: {"type": "token", "content": "..."} — LLM 输出的 token 片段
    - data: {"type": "tool_call", "name": "...", "args": {...}} — 工具调用
    - data: {"type": "done", "content": "..."} — 完整回复（结束标记）
    - data: {"type": "error", "message": "..."} — 错误
    """
    if agent_graph.graph is None:
        raise RuntimeError("Graph not initialized. Check lifespan startup.")

    config = {
        "configurable": {
            "thread_id": _build_thread_id(user_id, session_id),
        }
    }
    state = {
        "user_id": user_id,
        "session_id": session_id,
        "messages": [HumanMessage(content=text)],
    }

    logger.info("Stream request: user=%s session=%s", user_id, session_id)

    async def event_generator():
        full_content = ""
        try:
            async for event in agent_graph.graph.astream_events(
                state, config=config, version="v2"
            ):
                kind = event.get("event")

                # LLM 流式输出的 token 片段
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        full_content += chunk.content
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"

                # 工具调用事件
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_input}, ensure_ascii=False)}\n\n"

                # 工具执行完成
                elif kind == "on_tool_end":
                    tool_output = event.get("data", {}).get("output", "")
                    # tool output 可能是复杂对象，转为字符串
                    if hasattr(tool_output, "content"):
                        tool_output = tool_output.content
                    yield f"data: {json.dumps({'type': 'tool_result', 'content': str(tool_output)[:500]}, ensure_ascii=False)}\n\n"

            # 流结束
            yield f"data: {json.dumps({'type': 'done', 'content': full_content}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error("Stream error: %s", e, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )
