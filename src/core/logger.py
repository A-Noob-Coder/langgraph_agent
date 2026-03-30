# src/core/logger.py
"""
结构化日志模块。

统一的日志格式：[时间] [级别] [模块] 消息
所有模块使用 get_logger(__name__) 获取 logger 实例。
"""
import logging
import sys


def _setup_root_logger() -> None:
    """配置根 logger，仅执行一次。"""
    root = logging.getLogger("agent")
    if root.handlers:
        return  # 已配置过，跳过

    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


# 模块加载时初始化
_setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """获取命名 logger，继承 agent 根 logger 的配置。

    Usage:
        from src.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("服务启动")
    """
    return logging.getLogger(f"agent.{name}")
