"""
全局异常处理模块
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from logging import getLogger

logger = getLogger(__name__)


class AppException(Exception):
    """应用基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    """资源未找到异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class BadRequestException(AppException):
    """错误请求异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            details=details,
        )


class ValidationException(AppException):
    """验证异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class DataAccessException(AppException):
    """数据访问异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATA_ACCESS_ERROR",
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用异常处理器"""
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "details": exc.details,
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP 异常处理器"""
    logger.error(
        f"HTTP error: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.detail,
                "code": f"HTTP_{exc.status_code}",
            },
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "服务器内部错误",
                "code": "INTERNAL_SERVER_ERROR",
            },
        },
    )
