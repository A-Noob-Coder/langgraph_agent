# src/core/exception_handlers.py
"""
全局异常处理器。

统一 JSON 错误响应格式，防止内部 traceback 泄露。
"""
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logger import get_logger

logger = get_logger(__name__)


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """构建统一的错误响应。"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理已知的 HTTP 异常（如 404、401 等）。"""
    logger.warning("HTTP %d: %s | path=%s", exc.status_code, exc.detail, request.url.path)
    return _error_response(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        status_code=exc.status_code,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求参数校验失败。"""
    errors = exc.errors()
    logger.warning("Validation error: %s | path=%s", errors, request.url.path)
    # 提取第一个错误的简要信息
    first_error = errors[0] if errors else {}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "Invalid request")
    return _error_response(
        code="VALIDATION_ERROR",
        message=f"{field}: {msg}",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底处理所有未捕获异常，隐藏内部详情。"""
    logger.error(
        "Unhandled exception: %s | path=%s\n%s",
        str(exc),
        request.url.path,
        traceback.format_exc(),
    )
    return _error_response(
        code="INTERNAL_ERROR",
        message="服务内部错误，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """注册所有异常处理器到 FastAPI 应用。"""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
