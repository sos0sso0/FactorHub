"""
前端配置管理
"""

import os
from typing import List


def get_api_base_url() -> str:
    """获取 API 基础 URL"""
    return os.getenv("FACTORFLOW_API_URL", "http://localhost:8000")


def get_cors_origins() -> List[str]:
    """获取允许的 CORS 源"""
    origins_str = os.getenv("FACTORFLOW_CORS_ORIGINS", "")
    if origins_str:
        return [origin.strip() for origin in origins_str.split(",")]
    return ["http://localhost:8501", "http://localhost:3000"]
