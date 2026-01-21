"""
配置管理 - 使用环境变量
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""

    # 项目路径配置
    BASE_DIR: Path = Field(default=Path(__file__).resolve().parent.parent.parent)

    # 数据库配置
    DATABASE_URL: str = Field(default="sqlite:///./data/factor_flow.db")

    # API 配置
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)

    # CORS 配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Streamlit 配置
    STREAMLIT_HOST: str = "localhost"
    STREAMLIT_PORT: int = 8501

    # akshare 缓存配置
    AKSHARE_CACHE_ENABLED: bool = True
    AKSHARE_CACHE_DIR: Path = Field(default=Path("./data/cache/akshare"))

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 分析配置
    DEFAULT_ANALYSIS_WINDOW: int = 252
    DEFAULT_TEST_SIZE: float = 0.2
    SHAP_ENABLED: bool = True

    # 数据目录
    DATA_DIR: Path = Field(default=Path("./data"))
    CACHE_DIR: Path = Field(default=Path("./data/cache"))
    LOGS_DIR: Path = Field(default=Path("./logs"))
    CONFIG_DIR: Path = Field(default=Path("./config"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保路径是绝对路径
        self._setup_directories()

    def _setup_directories(self):
        """创建必要的目录"""
        # 转换为绝对路径
        if not self.DATA_DIR.is_absolute():
            self.DATA_DIR = self.BASE_DIR / self.DATA_DIR
        if not self.CACHE_DIR.is_absolute():
            self.CACHE_DIR = self.BASE_DIR / self.CACHE_DIR
        if not self.LOGS_DIR.is_absolute():
            self.LOGS_DIR = self.BASE_DIR / self.LOGS_DIR
        if not self.CONFIG_DIR.is_absolute():
            self.CONFIG_DIR = self.BASE_DIR / self.CONFIG_DIR
        if not self.AKSHARE_CACHE_DIR.is_absolute():
            self.AKSHARE_CACHE_DIR = self.BASE_DIR / self.AKSHARE_CACHE_DIR

        # 创建目录
        for dir_path in [
            self.DATA_DIR,
            self.CACHE_DIR,
            self.LOGS_DIR,
            self.CONFIG_DIR,
            self.AKSHARE_CACHE_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def factor_config_path(self) -> Path:
        """因子配置文件路径"""
        return self.CONFIG_DIR / "factors.yaml"

    @property
    def database_url(self) -> str:
        """数据库连接 URL"""
        # 如果是相对路径，转换为绝对路径
        if self.DATABASE_URL.startswith("sqlite:///"):
            db_path = self.DATABASE_URL.replace("sqlite:///", "")
            if not Path(db_path).is_absolute():
                abs_path = self.BASE_DIR / db_path
                return f"sqlite:///{abs_path}"
        return self.DATABASE_URL


# 全局配置实例
settings = Settings()


# 向后兼容 - 保持旧代码可工作
BASE_DIR = settings.BASE_DIR
DATABASE_URL = settings.database_url
DATA_DIR = settings.DATA_DIR
CACHE_DIR = settings.CACHE_DIR
LOGS_DIR = settings.LOGS_DIR
CONFIG_DIR = settings.CONFIG_DIR
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
STREAMLIT_HOST = settings.STREAMLIT_HOST
STREAMLIT_PORT = settings.STREAMLIT_PORT
AKSHARE_CACHE_ENABLED = settings.AKSHARE_CACHE_ENABLED
AKSHARE_CACHE_DIR = settings.AKSHARE_CACHE_DIR
FACTOR_CONFIG_PATH = settings.factor_config_path
LOG_LEVEL = settings.LOG_LEVEL
LOG_FORMAT = settings.LOG_FORMAT
