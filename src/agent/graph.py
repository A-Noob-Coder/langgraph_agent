# src/agent/graph.py
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    RemoveMessage,
    trim_messages,
)
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime

from src.agent.state import AgentState, Context
from src.agent.tools import tools
from src.agent.prompts import build_system_prompt
from src.core.config import settings

tool_node = ToolNode(tools)


# ── Token 估算函数 ──────────────────────────────────────────
def _estimate_tokens(messages: list) -> int:
    """基于字符长度的 token 估算，兼容所有模型。"""
    total_chars = 0
    for msg in messages:
        content = msg.content if hasattr(msg, "content") else str(msg)
        total_chars += len(content) if isinstance(content, str) else 0
        # 每条消息额外计算 role 等元数据开销（约 4 tokens）
        total_chars += 8
    return total_chars // 2


# ── LLM 客户端缓存 ──────────────────────────────────────────
@lru_cache(maxsize=4)
def _get_model(model_name: str, temperature: float):
    """缓存 LLM 客户端实例，相同参数返回同一对象。"""
    return init_chat_model(
        model=model_name,
        model_provider="openai",
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.siliconflow.cn/v1"),
    )


async def call_model(state: AgentState, runtime: Runtime[Context]) -> Dict[str, Any]:
    context = runtime.context or {}
    model_name = context.get("model_name", settings.MODEL_NAME)
    temperature = context.get("temperature", settings.TEMPERATURE)

    model = _get_model(model_name, temperature)
    model_with_tools = model.bind_tools(tools)

    messages = state["messages"]
    summary = state.get("summary", "")

    # 判断当前消息列表中是否已经有系统提示词
    # 把系统提示词替换为动态挂载有 summary 的长记忆版本
    sys_msg = build_system_prompt(summary)
    if messages and isinstance(messages[0], SystemMessage):
        messages = [sys_msg] + messages[1:]
    else:
        messages = [sys_msg] + messages

    # ── 消息窗口最后防线防崩 ──────────────────────────────────
    trimmed = trim_messages(
        messages,
        max_tokens=settings.MAX_CONTEXT_TOKENS,
        strategy="last",
        token_counter=_estimate_tokens,
        include_system=True,
    )

    # 安全回退：如果 trim 后没有 HumanMessage，使用原始消息（避免 API 拒绝）
    has_human = any(isinstance(m, HumanMessage) for m in trimmed)
    messages = trimmed if has_human else messages

    response = await model_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def call_tools(state: AgentState, runtime: Runtime[Context]) -> Dict[str, Any]:
    try:
        result = await tool_node.ainvoke(state)
        return result
    except Exception as e:
        return {"error": f"工具调用失败: {e}"}


# ── Phase 3.1 核心攻坚：长短记忆滚动摘要引擎 ──────────────────────
async def summarize_conversation(state: AgentState, runtime: Runtime[Context]) -> Dict[str, Any]:
    """异步长短记忆分离节点：将老对话生成摘要，并从数据库物理清理。"""
    summary = state.get("summary", "")
    messages = state["messages"]

    context = runtime.context or {}
    model_name = context.get("model_name", settings.MODEL_NAME)
    temperature = context.get("temperature", settings.TEMPERATURE)
    model = _get_model(model_name, temperature)

    # 1. 提取早期的历史记录进行总结（保留最近的 4 条消息作为高保真工作区窗口）
    messages_to_summarize = messages[:-4]
    
    # 2. 剃刀原则：只总结人类和AI的核心事实，过滤系统指令、复杂长 JSON 的 Tool 调用细节
    filtered_messages = []
    for m in messages_to_summarize:
        if isinstance(m, SystemMessage) or isinstance(m, ToolMessage):
            continue
        # 丢弃发起工具调用的 AIMessage，否则只有发起、没有结果会导致后续出现 400 Context 断代报错
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            continue
        filtered_messages.append(m)

    # 3. 让大模型进行总结交织
    new_summary = summary
    if filtered_messages:
        summary_prompt = (
            f"以下是你之前的历史档案（如果有）：\n{summary}\n\n"
            "请将下方新发生的一串对话，以第三人称浓缩并更新到前面的历史档案中。"
            "需保持客观、简练，保留用户的核心特征、偏好和讨论过的核心事件，不要输出套话废话：\n\n"
        )
        for m in filtered_messages:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            content = m.content if isinstance(m.content, str) else str(m.content)
            summary_prompt += f"{role}: {content}\n"

        response = await model.ainvoke([HumanMessage(content=summary_prompt)])
        new_summary = response.content

    # 4. 最关键的一步：生成特殊的 RemoveMessage 标记，利用框架层的 Postgres 底层彻底物理清理过期冗余记录
    delete_messages = [RemoveMessage(id=m.id) for m in messages_to_summarize if m.id]

    # 直接返回字典，LangGraph 的 List Reducer（add_messages）会根据 RemoveMessage 自动删、对 summary 自动覆盖
    return {"summary": new_summary, "messages": delete_messages}


def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1]

    # 有工具调用需求必须优先走工具节点
    if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
        return "tools"

    # 如果消息总数超过 10 条（大概就是五次左右的问答回合），我们触发一次后台摘要重组清理过程。
    # 这里阈值如果设得太大，总结的跨度太长；设得太小，API支出增加。为了目前方便演示与测试设在 10 头上。
    if len(messages) > 10:
        return "summarize_conversation"

    return "__end__"


def build_agent_graph(checkpointer):
    """构建并编译 Agent Graph"""
    graph_builder = StateGraph(AgentState, context_schema=Context)

    graph_builder.add_node("agent", call_model)
    graph_builder.add_node("tools", call_tools)
    graph_builder.add_node("summarize_conversation", summarize_conversation)  # 挂载新节点

    graph_builder.add_edge("__start__", "agent")
    
    # 根据 condition 控制大血管走向
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "summarize_conversation": "summarize_conversation",
            "__end__": "__end__",
        },
    )
    graph_builder.add_edge("tools", "agent")
    
    # 总结完成后自动休眠
    graph_builder.add_edge("summarize_conversation", "__end__")

    return graph_builder.compile(
        name="Enterprise Agent with Rolling Memory",
        checkpointer=checkpointer
    )

# 全局图实例
graph = None
