"""
数据库模型定义
使用 SQLAlchemy ORM 定义因子和数据的数据库结构
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Factor(Base):
    """因子表"""
    __tablename__ = "factors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    formula = Column(Text, nullable=False)
    description = Column(Text)
    source = Column(String(20), nullable=False, default="user")  # system 或 user
    category = Column(String(50))  # 因子分类：price_return, momentum, volatility, volume, pattern
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "formula": self.formula,
            "description": self.description,
            "source": self.source,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalysisTask(Base):
    """分析任务表"""
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(200))
    mode = Column(String(20))  # single 或 pool
    symbols = Column(Text)  # JSON 字符串存储股票代码列表
    factors = Column(Text)  # JSON 字符串存储选择的因子列表
    start_date = Column(String(20))
    end_date = Column(String(20))
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result_path = Column(Text)  # 分析结果存储路径
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "mode": self.mode,
            "symbols": self.symbols,
            "factors": self.factors,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "result_path": self.result_path,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DataCache(Base):
    """数据缓存表"""
    __tablename__ = "data_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    data_type = Column(String(20), nullable=False)  # daily, weekly, etc
    start_date = Column(String(20))
    end_date = Column(String(20))
    file_path = Column(Text)  # 缓存文件路径
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "data_type": self.data_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
