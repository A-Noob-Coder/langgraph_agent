# src/agent/prompts.py
from langchain_core.messages import SystemMessage

def build_system_prompt(summary: str = "") -> SystemMessage:
    """动态构建带长期记忆的系统提示词"""
    content = """
你是一个智能助手。

在回答问题时：
1. 如果需要获取最新消息，使用 tavily_search 工具进行搜索。
2. 如果需要确认当前时间，使用 get_current_datetime 工具。
3. 在解读搜索结果时，要根据当前日期正确理解相对时间(今天、明天、昨天等)
4. 回答要准确、完整、基于搜索到的最新信息。
    """.strip()

    # 将长线压缩的过往聊天记忆无缝拼接到系统人格设定中
    if summary:
        content += f"\n\n### 【历史前情提要 / 用户画像设定】\n由于对话过长，此前的早期交互已被系统压缩如下，请将其作为与用户对话的已知背景上下文：\n{summary}"

    return SystemMessage(content=content)
