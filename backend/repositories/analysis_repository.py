"""
分析任务仓储层 - 封装分析任务数据访问逻辑
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from backend.models import AnalysisTask
from backend.core.exceptions import DataAccessException, NotFoundException
import logging

logger = logging.getLogger(__name__)


class AnalysisRepository:
    """分析任务数据访问仓储"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, task_id: int) -> Optional[AnalysisTask]:
        """根据 ID 查找任务"""
        try:
            return (
                self.db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            )
        except Exception as e:
            logger.error(f"查询任务失败 (ID: {task_id}): {e}")
            raise DataAccessException(f"查询任务失败: {str(e)}")

    def find_all(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AnalysisTask]:
        """查询任务列表"""
        try:
            query = self.db.query(AnalysisTask)

            if status:
                query = query.filter(AnalysisTask.status == status)

            return query.order_by(AnalysisTask.created_at.desc()).offset(offset).limit(
                limit
            ).all()
        except Exception as e:
            logger.error(f"查询任务列表失败: {e}")
            raise DataAccessException(f"查询任务列表失败: {str(e)}")

    def create(
        self,
        task_name: str,
        mode: str,
        symbols: List[str],
        factors: List[str],
        start_date: str,
        end_date: str,
    ) -> AnalysisTask:
        """创建分析任务"""
        try:
            import json

            task = AnalysisTask(
                task_name=task_name,
                mode=mode,
                symbols=json.dumps(symbols),
                factors=json.dumps(factors),
                start_date=start_date,
                end_date=end_date,
                status="pending",
            )

            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"创建分析任务: {task_name}")
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建分析任务失败: {e}")
            raise DataAccessException(f"创建分析任务失败: {str(e)}")

    def update_status(
        self,
        task_id: int,
        status: str,
        result_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AnalysisTask:
        """更新任务状态"""
        try:
            task = self.find_by_id(task_id)
            if not task:
                raise NotFoundException(f"任务 ID {task_id} 不存在")

            task.status = status
            if result_path is not None:
                task.result_path = result_path
            if error_message is not None:
                task.error_message = error_message

            self.db.commit()
            self.db.refresh(task)
            logger.info(f"更新任务状态: {task_id} -> {status}")
            return task
        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务状态失败: {e}")
            raise DataAccessException(f"更新任务状态失败: {str(e)}")
