"""
因子仓储层 - 封装因子数据访问逻辑
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.models import Factor
from backend.core.exceptions import DataAccessException, NotFoundException
import logging

logger = logging.getLogger(__name__)


class FactorRepository:
    """因子数据访问仓储"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, factor_id: int) -> Optional[Factor]:
        """根据 ID 查找因子"""
        try:
            return self.db.query(Factor).filter(Factor.id == factor_id).first()
        except Exception as e:
            logger.error(f"查询因子失败 (ID: {factor_id}): {e}")
            raise DataAccessException(f"查询因子失败: {str(e)}")

    def find_by_name(self, name: str) -> Optional[Factor]:
        """根据名称查找因子"""
        try:
            return self.db.query(Factor).filter(Factor.name == name).first()
        except Exception as e:
            logger.error(f"查询因子失败 (名称: {name}): {e}")
            raise DataAccessException(f"查询因子失败: {str(e)}")

    def find_all(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
    ) -> List[Factor]:
        """查询所有因子"""
        try:
            query = self.db.query(Factor)

            if source:
                query = query.filter(Factor.source == source)
            if category:
                query = query.filter(Factor.category == category)
            query = query.filter(Factor.is_active == is_active)

            return query.all()
        except Exception as e:
            logger.error(f"查询因子列表失败: {e}")
            raise DataAccessException(f"查询因子列表失败: {str(e)}")

    def get_stats(self) -> Dict[str, any]:
        """获取因子统计信息"""
        try:
            total = self.db.query(Factor).filter(Factor.is_active == True).count()
            system_count = (
                self.db.query(Factor)
                .filter(Factor.source == "system", Factor.is_active == True)
                .count()
            )
            user_count = (
                self.db.query(Factor)
                .filter(Factor.source == "user", Factor.is_active == True)
                .count()
            )

            # 按分类统计
            categories = {}
            for factor in self.db.query(Factor).filter(Factor.is_active == True).all():
                category = factor.category or "未分类"
                categories[category] = categories.get(category, 0) + 1

            return {
                "total": total,
                "system_count": system_count,
                "user_count": user_count,
                "categories": categories,
            }
        except Exception as e:
            logger.error(f"获取因子统计失败: {e}")
            raise DataAccessException(f"获取因子统计失败: {str(e)}")

    def create(self, factor: Factor) -> Factor:
        """创建因子"""
        try:
            # 检查名称是否已存在
            existing = self.find_by_name(factor.name)
            if existing:
                raise DataAccessException(f"因子名称 '{factor.name}' 已存在")

            self.db.add(factor)
            self.db.commit()
            self.db.refresh(factor)
            logger.info(f"创建因子: {factor.name}")
            return factor
        except DataAccessException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建因子失败: {e}")
            raise DataAccessException(f"创建因子失败: {str(e)}")

    def update(
        self,
        factor_id: int,
        name: Optional[str] = None,
        formula: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Factor:
        """更新因子"""
        try:
            factor = self.find_by_id(factor_id)
            if not factor:
                raise NotFoundException(f"因子 ID {factor_id} 不存在")

            if factor.source == "system":
                raise DataAccessException("系统预置因子不可修改")

            if name is not None:
                factor.name = name
            if formula is not None:
                factor.formula = formula
            if description is not None:
                factor.description = description
            if category is not None:
                factor.category = category

            self.db.commit()
            self.db.refresh(factor)
            logger.info(f"更新因子: {factor_id}")
            return factor
        except NotFoundException:
            raise
        except DataAccessException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新因子失败: {e}")
            raise DataAccessException(f"更新因子失败: {str(e)}")

    def delete(self, factor_id: int) -> bool:
        """删除因子（软删除）"""
        try:
            factor = self.find_by_id(factor_id)
            if not factor:
                raise NotFoundException(f"因子 ID {factor_id} 不存在")

            if factor.source == "system":
                raise DataAccessException("系统预置因子不可删除")

            factor.is_active = False
            self.db.commit()
            logger.info(f"删除因子: {factor_id}")
            return True
        except NotFoundException:
            raise
        except DataAccessException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除因子失败: {e}")
            raise DataAccessException(f"删除因子失败: {str(e)}")

    def batch_create(self, factors: List[Factor]) -> int:
        """批量创建因子"""
        try:
            count = 0
            for factor in factors:
                # 检查是否已存在
                existing = self.find_by_name(factor.name)
                if not existing:
                    self.db.add(factor)
                    count += 1

            if count > 0:
                self.db.commit()
                logger.info(f"批量创建因子: {count} 个")

            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"批量创建因子失败: {e}")
            raise DataAccessException(f"批量创建因子失败: {str(e)}")
