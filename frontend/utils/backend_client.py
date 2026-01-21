"""
后端服务直接调用客户端
绕过 HTTP API，直接调用后端服务模块
"""

from typing import Dict, List, Optional
import logging

# 导入后端服务模块
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services import factor_service, analysis_service, data_service
from backend.core.database import get_db_session

logger = logging.getLogger(__name__)


class BackendClient:
    """后端服务客户端（直接调用）"""

    def __init__(self):
        """初始化客户端"""
        # 初始化数据库和系统因子
        self._initialized = False

    def _ensure_initialized(self):
        """确保后端服务已初始化"""
        if not self._initialized:
            try:
                from backend.core.database import init_db
                init_db()
                factor_service.init_system_factors()
                self._initialized = True
                logger.info("后端服务初始化完成")
            except Exception as e:
                logger.error(f"后端服务初始化失败: {e}")
                raise

    # 健康检查
    def health_check(self) -> Dict:
        """健康检查"""
        self._ensure_initialized()
        return {"status": "ok", "backend": "direct"}

    # 因子管理
    def get_factors(self, source: Optional[str] = None) -> Dict:
        """获取因子列表"""
        self._ensure_initialized()
        try:
            with get_db_session() as db:
                from backend.repositories import FactorRepository

                repo = FactorRepository(db)
                if source:
                    factors = repo.find_by_source(source)
                else:
                    factors = repo.find_all()

                return {
                    "success": True,
                    "data": [
                        {
                            "id": f.id,
                            "name": f.name,
                            "description": f.description,
                            "formula": f.formula,
                            "category": f.category,
                            "source": f.source,
                            "created_at": f.created_at.isoformat() if f.created_at else None,
                        }
                        for f in factors
                    ],
                }
        except Exception as e:
            logger.error(f"获取因子列表失败: {e}")
            return {"success": False, "detail": str(e)}

    def get_factor_stats(self) -> Dict:
        """获取因子统计"""
        self._ensure_initialized()
        try:
            with get_db_session() as db:
                from backend.repositories import FactorRepository

                repo = FactorRepository(db)
                total = repo.count()

                # 统计来源
                system_count = repo.count_by_source("system")
                user_count = repo.count_by_source("user")

                # 统计分类
                factors = repo.find_all()
                categories = {}
                for f in factors:
                    categories[f.category] = categories.get(f.category, 0) + 1

                return {
                    "success": True,
                    "data": {
                        "total": total,
                        "system_count": system_count,
                        "user_count": user_count,
                        "categories": categories,
                    },
                }
        except Exception as e:
            logger.error(f"获取因子统计失败: {e}")
            return {"success": False, "detail": str(e)}

    def create_factor(
        self, name: str, formula: str, description: str, category: str
    ) -> Dict:
        """创建因子"""
        self._ensure_initialized()
        try:
            with get_db_session() as db:
                from backend.repositories import FactorRepository
                from backend.models import Factor

                repo = FactorRepository(db)

                # 检查是否已存在
                existing = repo.find_by_name(name)
                if existing:
                    return {"success": False, "detail": f"因子 '{name}' 已存在"}

                # 创建因子
                factor = Factor(
                    name=name,
                    formula=formula,
                    description=description,
                    category=category,
                    source="user",
                )

                created = repo.create(factor)

                return {
                    "success": True,
                    "data": {
                        "id": created.id,
                        "name": created.name,
                    },
                }
        except Exception as e:
            logger.error(f"创建因子失败: {e}")
            return {"success": False, "detail": str(e)}

    def update_factor(
        self,
        factor_id: int,
        name: Optional[str] = None,
        formula: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict:
        """更新因子"""
        self._ensure_initialized()
        try:
            with get_db_session() as db:
                from backend.repositories import FactorRepository

                repo = FactorRepository(db)

                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if formula is not None:
                    update_data["formula"] = formula
                if description is not None:
                    update_data["description"] = description
                if category is not None:
                    update_data["category"] = category

                updated = repo.update(factor_id, **update_data)

                return {
                    "success": True,
                    "data": {
                        "id": updated.id,
                        "name": updated.name,
                    },
                }
        except Exception as e:
            logger.error(f"更新因子失败: {e}")
            return {"success": False, "detail": str(e)}

    def delete_factor(self, factor_id: int) -> Dict:
        """删除因子"""
        self._ensure_initialized()
        try:
            with get_db_session() as db:
                from backend.repositories import FactorRepository

                repo = FactorRepository(db)
                repo.delete(factor_id)

                return {"success": True}
        except Exception as e:
            logger.error(f"删除因子失败: {e}")
            return {"success": False, "detail": str(e)}

    def validate_formula(self, formula: str) -> Dict:
        """验证因子公式"""
        self._ensure_initialized()
        try:
            result = factor_service.validate_formula(formula)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"验证公式失败: {e}")
            return {"success": False, "detail": str(e)}

    # 数据获取
    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """获取市场数据"""
        self._ensure_initialized()
        try:
            df = data_service.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "records": len(df),
                    "columns": list(df.columns),
                },
            }
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {"success": False, "detail": str(e)}

    # 分析
    def run_analysis(
        self,
        symbols: List[str],
        factors: List[str],
        start_date: str,
        end_date: str,
        mode: str = "pool",
    ) -> Dict:
        """执行因子分析"""
        self._ensure_initialized()
        try:
            results = analysis_service.execute_analysis(
                symbols=symbols,
                factors=factors,
                start_date=start_date,
                end_date=end_date,
                mode=mode,
            )

            return {"success": True, "data": results}
        except Exception as e:
            logger.error(f"执行分析失败: {e}")
            return {"success": False, "detail": str(e)}

    def compute_factors(self, symbol: str, factors: List[str]) -> Dict:
        """计算因子值"""
        self._ensure_initialized()
        try:
            result = analysis_service.compute_factors_for_symbol(symbol, factors)
            return result
        except Exception as e:
            logger.error(f"计算因子失败: {e}")
            return {"success": False, "detail": str(e)}


# 全局客户端实例
backend_client = BackendClient()
