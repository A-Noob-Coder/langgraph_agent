# src/agent/state.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    """LangGraph 状态：多轮对话 + 滚动摘要 + 元信息。"""
    user_id: str
    session_id: str
    summary: str  # 新增：用于存储跨越长周期的背景长期记忆提要
    messages: Annotated[list[AnyMessage], add_messages]

class Context(TypedDict):
    """运行时上下文（可从 API / config 透传）。"""
    model_name: str
    temperature: float
