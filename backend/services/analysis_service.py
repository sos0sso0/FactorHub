"""
分析服务层 - 封装因子分析业务逻辑
"""

from typing import List, Dict, Optional
import logging

from backend.core.analyzer import FactorAnalyzer
from backend.core.exceptions import NotFoundException, ValidationException
from backend.services.data_service import data_service
from backend.services.factor_service import factor_service

logger = logging.getLogger(__name__)


class AnalysisService:
    """因子分析业务服务"""

    def __init__(self):
        pass

    def execute_analysis(
        self,
        symbols: List[str],
        factors: List[str],
        start_date: str,
        end_date: str,
        mode: str = "pool",
    ) -> Dict:
        """
        执行因子分析

        Args:
            symbols: 品种代码列表
            factors: 因子名称列表
            start_date: 开始日期
            end_date: 结束日期
            mode: 分析模式 (single 或 pool)

        Returns:
            分析结果字典
        """
        if not symbols:
            raise ValidationException("品种代码列表不能为空")
        if not factors:
            raise ValidationException("因子列表不能为空")

        # 获取数据
        logger.info(f"获取数据: {symbols}")
        data_dict = data_service.get_multiple_symbols(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            use_cache=True,
        )

        if not data_dict:
            raise NotFoundException("无法获取数据")

        # 准备分析结果
        results = {
            "symbols": symbols,
            "factors": factors,
            "start_date": start_date,
            "end_date": end_date,
            "analysis_results": {},
        }

        # 对每个品种进行分析
        for symbol, df in data_dict.items():
            try:
                logger.info(f"分析品种: {symbol}")
                symbol_result = self._analyze_single_symbol(
                    df=df, symbol=symbol, factors=factors
                )
                results["analysis_results"][symbol] = symbol_result

            except Exception as e:
                logger.error(f"分析 {symbol} 失败: {e}")
                results["analysis_results"][symbol] = {"error": str(e)}

        return results

    def _analyze_single_symbol(
        self, df, symbol: str, factors: List[str]
    ) -> Dict:
        """分析单个品种"""
        try:
            # 计算因子
            logger.info(f"计算因子: {factors}")
            df_with_factors = factor_service.compute_factors(df, factors)

            # 检查哪些因子成功计算
            computed_factors = [f for f in factors if f in df_with_factors.columns]
            if not computed_factors:
                return {"error": f"没有成功计算的因子。请求的因子: {factors}"}

            logger.info(f"成功计算的因子: {computed_factors}")

            # 准备特征（标准化）
            analyzer = FactorAnalyzer()
            df_prepared = analyzer.prepare_features(df_with_factors, computed_factors)

            # 检查标准化后的特征
            feature_names = [f"{f}_std" for f in computed_factors if f"{f}_std" in df_prepared.columns]
            if not feature_names:
                return {"error": f"没有可用的标准化特征。可用因子: {computed_factors}"}

            logger.info(f"标准化特征: {feature_names}")

            # 检查数据量是否足够
            if len(df_prepared) < 50:
                return {"error": f"数据量不足，至少需要50条数据，当前只有{len(df_prepared)}条"}

            # 训练模型
            train_results = analyzer.train_model(df_prepared, feature_names)

            # 计算 IC
            ic_results = {}
            for factor in computed_factors:
                factor_std = f"{factor}_std"
                if factor_std in df_prepared.columns:
                    ic_results[factor] = analyzer.calculate_ic(df_prepared, factor_std)

            # SHAP 分析
            shap_summary = analyzer.get_shap_summary()

            logger.info(f"分析完成: R²(train)={train_results['train_r2']:.4f}, R²(test)={train_results['test_r2']:.4f}")

            return {
                "train_results": train_results,
                "ic_results": ic_results,
                "shap_summary": shap_summary,
                "computed_factors": computed_factors,
            }

        except Exception as e:
            logger.error(f"分析失败: {e}", exc_info=True)
            return {"error": f"分析异常: {str(e)}"}

    def compute_factors_for_symbol(
        self, symbol: str, factor_names: List[str]
    ) -> Dict:
        """为指定品种计算因子"""
        try:
            # 获取数据
            df = data_service.get_futures_data(symbol=symbol)

            # 计算因子
            df_with_factors = factor_service.compute_factors(df, factor_names)

            return {
                "success": True,
                "data": df_with_factors.reset_index().to_dict(orient="records"),
            }

        except Exception as e:
            logger.error(f"计算因子失败: {e}")
            raise


# 全局分析服务实例
analysis_service = AnalysisService()
