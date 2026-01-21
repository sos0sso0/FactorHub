"""
因子服务层 - 封装因子相关业务逻辑
"""

from typing import List, Optional, Dict
from pathlib import Path
import pandas as pd
import numpy as np
import talib
import yaml
import logging

from backend.core.database import get_db_session
from backend.core.settings import settings
from backend.core.exceptions import ValidationException
from backend.repositories import FactorRepository
from backend.models import Factor

logger = logging.getLogger(__name__)


class FactorService:
    """因子业务服务"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化因子服务

        Args:
            config_path: 因子配置文件路径，如果不指定则使用默认路径
        """
        self.config_path = config_path or settings.factor_config_path
        self.factors_config = self._load_factors_config()

    def _load_factors_config(self) -> Dict:
        """从 YAML 配置文件加载因子定义"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"成功加载因子配置: {self.config_path}")
            return config or {}
        except Exception as e:
            logger.error(f"加载因子配置失败: {e}")
            return {}

    def init_system_factors(self) -> int:
        """初始化系统预置因子到数据库"""
        db = get_db_session()
        try:
            repo = FactorRepository(db)
            all_factors = []

            # 从配置文件加载所有因子
            for category, factors in self.factors_config.items():
                for factor_def in factors:
                    # 检查因子是否已存在
                    existing = repo.find_by_name(factor_def["name"])
                    if not existing:
                        factor = Factor(
                            name=factor_def["name"],
                            formula=factor_def["formula"],
                            description=factor_def.get("description", ""),
                            source="system",
                            category=category.replace("_factors", ""),
                        )
                        all_factors.append(factor)

            # 批量添加
            count = repo.batch_create(all_factors)
            logger.info(f"初始化系统因子: {count} 个")
            return count

        except Exception as e:
            logger.error(f"初始化系统因子失败: {e}")
            raise
        finally:
            db.close()

    def get_all_factors(self, source: Optional[str] = None) -> List[Dict]:
        """获取所有因子"""
        db = get_db_session()
        try:
            repo = FactorRepository(db)
            factors = repo.find_all(source=source)
            return [factor.to_dict() for factor in factors]
        finally:
            db.close()

    def get_factor_stats(self) -> Dict:
        """获取因子统计信息"""
        db = get_db_session()
        try:
            repo = FactorRepository(db)
            return repo.get_stats()
        finally:
            db.close()

    def add_factor(
        self, name: str, formula: str, description: str, category: str = None
    ) -> bool:
        """添加用户自定义因子"""
        db = get_db_session()
        try:
            repo = FactorRepository(db)

            # 验证公式
            validation_result = self.validate_formula(formula)
            if not validation_result["valid"]:
                raise ValidationException(
                    f"公式验证失败: {validation_result['error']}"
                )

            factor = Factor(
                name=name,
                formula=formula,
                description=description,
                source="user",
                category=category or "custom",
            )

            repo.create(factor)
            return True

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"添加因子失败: {e}")
            raise
        finally:
            db.close()

    def update_factor(
        self,
        factor_id: int,
        name: Optional[str] = None,
        formula: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        """更新用户因子"""
        db = get_db_session()
        try:
            repo = FactorRepository(db)

            # 如果提供了公式，先验证
            if formula:
                validation_result = self.validate_formula(formula)
                if not validation_result["valid"]:
                    raise ValidationException(
                        f"公式验证失败: {validation_result['error']}"
                    )

            repo.update(factor_id, name, formula, description, category)
            return True

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"更新因子失败: {e}")
            raise
        finally:
            db.close()

    def delete_factor(self, factor_id: int) -> bool:
        """删除用户因子"""
        db = get_db_session()
        try:
            repo = FactorRepository(db)
            repo.delete(factor_id)
            return True
        except Exception as e:
            logger.error(f"删除因子失败: {e}")
            raise
        finally:
            db.close()

    def validate_formula(self, formula: str) -> Dict:
        """验证因子公式"""
        try:
            # 创建测试 DataFrame
            test_df = pd.DataFrame(
                {
                    "open": np.random.rand(100) * 100 + 100,
                    "high": np.random.rand(100) * 100 + 110,
                    "low": np.random.rand(100) * 100 + 90,
                    "close": np.random.rand(100) * 100 + 100,
                    "volume": np.random.randint(1000, 10000, 100),
                }
            )

            # 尝试执行公式
            df = test_df.copy()
            result = eval(formula, {"np": np, "pd": pd, "talib": talib, "df": df})

            # 检查结果
            if isinstance(result, pd.Series):
                return {"valid": True, "error": None}
            else:
                return {"valid": False, "error": "公式必须返回 pandas Series"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def compute_factors(
        self, df: pd.DataFrame, factor_names: List[str]
    ) -> pd.DataFrame:
        """计算指定因子"""
        result_df = df.copy()
        db = get_db_session()

        try:
            repo = FactorRepository(db)

            for factor_name in factor_names:
                try:
                    factor = repo.find_by_name(factor_name)

                    if not factor:
                        logger.warning(f"因子不存在: {factor_name}")
                        continue

                    # 计算因子
                    df_copy = df.copy()
                    factor_value = eval(
                        factor.formula,
                        {"np": np, "pd": pd, "talib": talib, "df": df_copy},
                    )

                    if isinstance(factor_value, pd.Series):
                        result_df[factor_name] = factor_value.values
                    else:
                        result_df[factor_name] = factor_value

                except Exception as e:
                    logger.error(f"计算因子 {factor_name} 失败: {e}")

            return result_df

        finally:
            db.close()


# 全局因子服务实例
factor_service = FactorService()
