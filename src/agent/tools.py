# src/agent/tools.py
from datetime import datetime
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from src.core.config import settings

@tool
def get_current_datetime() -> str:
    """获取当前日期和时间。"""
    now = datetime.now()
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}, 星期{weekdays[now.weekday()]}"

tavily_tool = TavilySearch(
    max_result=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=False,
    topic="news",
    tavily_api_key=settings.TAVILY_API_KEY,
)

tools = [tavily_tool, get_current_datetime]
