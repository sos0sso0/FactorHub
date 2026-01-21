"""
数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models import Base
from backend.core.settings import settings
import logging

logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    echo=False,  # 设置为 True 可以看到 SQL 语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建所有表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


def get_db() -> Session:
    """
    获取数据库会话
    用于 FastAPI 依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    获取数据库会话（同步版本）
    用于直接调用
    """
    return SessionLocal()
