"""
组合分析服务 - 分析投资组合的暴露度和风险
"""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class PortfolioAnalysisService:
    """组合分析服务"""

    def __init__(self):
        pass

    def calculate_industry_exposure(
        self,
        positions: pd.DataFrame,
        industry_column: str = "industry",
        weight_column: str = "weight"
    ) -> Dict:
        """
        计算行业暴露度

        Args:
            positions: 持仓DataFrame，包含股票和权重
            industry_column: 行业列名
            weight_column: 权重列名

        Returns:
            行业暴露度字典
        """
        if industry_column not in positions.columns:
            return {"error": f"数据中缺少 {industry_column} 列"}

        if weight_column not in positions.columns:
            return {"error": f"数据中缺少 {weight_column} 列"}

        # 按行业汇总权重（假设每个股票只出现一次，取第一条记录的权重）
        industry_weights = positions.groupby(industry_column)[weight_column].first()

        # 归一化
        total_weight = industry_weights.sum()
        if total_weight > 0:
            industry_exposure = industry_weights / total_weight
        else:
            industry_exposure = industry_weights

        # 转换为字典
        result = {
            "industry_exposure": industry_exposure.to_dict(),
            "max_exposure": float(industry_exposure.max()),
            "min_exposure": float(industry_exposure.min()),
            "concentration": float(industry_exposure.std()),
        }

        # 计算集中度（前3大行业占比）
        top3_exposure = industry_exposure.nlargest(3).sum()
        result["top3_concentration"] = float(top3_exposure)

        return result

    def calculate_factor_exposure(
        self,
        positions: pd.DataFrame,
        factor_data: Dict[str, pd.Series],
        weight_column: str = "weight",
    ) -> Dict:
        """
        计算因子暴露度

        Args:
            positions: 持仓DataFrame，包含股票和权重
            factor_data: 因子数据字典 {factor_name: factor_values}
            weight_column: 权重列名

        Returns:
            因子暴露度字典
        """
        factor_exposures = {}

        # 获取唯一的股票列表和对应的权重（假设每个股票只取第一条记录）
        if weight_column in positions.columns:
            stock_weights = positions.groupby("stock_code")[weight_column].first()
        else:
            return {"error": f"数据中缺少 {weight_column} 列"}

        for factor_name, factor_values in factor_data.items():
            try:
                # 如果因子值是时间序列，取最后一个值（当前值）
                if isinstance(factor_values, pd.Series):
                    factor_value = factor_values.iloc[-1]
                else:
                    factor_value = factor_values

                # 加权平均因子值（简化版：假设所有股票的因子值相同）
                weighted_factor = (stock_weights * factor_value).sum()
                factor_exposures[factor_name] = float(weighted_factor)

            except Exception as e:
                # 跳过计算失败的因子
                continue

        return {
            "factor_exposures": factor_exposures,
            "max_exposure": max([abs(v) for v in factor_exposures.values()]) if factor_exposures else 0.0,
        }

    def calculate_concentration(
        self,
        positions: pd.DataFrame,
        weight_column: str = "weight"
    ) -> Dict:
        """
        计算组合集中度

        Args:
            positions: 持仓DataFrame
            weight_column: 权重列名

        Returns:
            集中度指标
        """
        if weight_column not in positions.columns:
            return {"error": f"数据中缺少 {weight_column} 列"}

        weights = positions[weight_column].abs().dropna()

        if len(weights) == 0:
            return {
                "top10_concentration": 0.0,
                "herfindahl_index": 0.0,
                "gini_coefficient": 0.0,
            }

        # 1. 前十大持仓占比
        weights_sorted = weights.sort_values(ascending=False)
        top10_concentration = weights_sorted.head(10).sum() / weights.sum()

        # 2. Herfindahl指数（权重平方和）
        normalized_weights = weights / weights.sum()
        herfindahl_index = (normalized_weights ** 2).sum()

        # 3. 基尼系数
        gini_coefficient = self._calculate_gini(normalized_weights.values)

        return {
            "top10_concentration": float(top10_concentration),
            "herfindahl_index": float(herfindahl_index),
            "gini_coefficient": float(gini_coefficient),
        }

    def _calculate_gini(self, values: np.ndarray) -> float:
        """
        计算基尼系数

        Args:
            values: 权重值数组

        Returns:
            基尼系数
        """
        sorted_values = np.sort(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

    def calculate_risk_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        annual_trading_days: int = 252,
    ) -> Dict:
        """
        计算组合风险指标

        Args:
            returns: 组合收益率序列
            benchmark_returns: 基准收益率序列（可选）
            annual_trading_days: 年化交易日数

        Returns:
            风险指标字典
        """
        returns_clean = returns.dropna()

        if len(returns_clean) == 0:
            return self._empty_risk_metrics()

        # 波动率
        volatility = returns_clean.std() * np.sqrt(annual_trading_days)

        # 下行波动率
        downside_returns = returns_clean[returns_clean < 0]
        downside_volatility = (
            downside_returns.std() * np.sqrt(annual_trading_days)
            if len(downside_returns) > 0
            else 0.0
        )

        # VaR (95%置信度)
        var_95 = returns_clean.quantile(0.05)

        # CVaR (条件VaR)
        cvar_95 = returns_clean[returns_clean <= var_95].mean()

        # 最大回撤
        cumulative = (1 + returns_clean).cumprod()
        peak = cumulative.cummax()
        drawdown = (peak - cumulative) / peak
        max_drawdown = drawdown.max()

        result = {
            "volatility": float(volatility),
            "downside_volatility": float(downside_volatility),
            "var_95": float(var_95),
            "cvar_95": float(cvar_95),
            "max_drawdown": float(max_drawdown),
        }

        # 如果有基准，计算相对风险指标
        if benchmark_returns is not None:
            aligned_data = pd.DataFrame({
                "portfolio": returns_clean,
                "benchmark": benchmark_returns
            }).dropna()

            if len(aligned_data) > 0:
                # 跟踪误差
                excess_returns = aligned_data["portfolio"] - aligned_data["benchmark"]
                tracking_error = excess_returns.std() * np.sqrt(annual_trading_days)

                # Beta
                covariance = aligned_data["portfolio"].cov(aligned_data["benchmark"])
                benchmark_variance = aligned_data["benchmark"].var()
                beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0

                result["tracking_error"] = float(tracking_error)
                result["beta"] = float(beta)

        return result

    def _empty_risk_metrics(self) -> Dict:
        """返回空的风险指标"""
        return {
            "volatility": 0.0,
            "downside_volatility": 0.0,
            "var_95": 0.0,
            "cvar_95": 0.0,
            "max_drawdown": 0.0,
        }

    def analyze_portfolio_comprehensive(
        self,
        positions: pd.DataFrame,
        returns: pd.Series,
        factor_data: Optional[Dict[str, pd.Series]] = None,
        benchmark_returns: Optional[pd.Series] = None,
    ) -> Dict:
        """
        综合分析投资组合

        Args:
            positions: 持仓数据
            returns: 收益率序列
            factor_data: 因子数据（可选）
            benchmark_returns: 基准收益率（可选）

        Returns:
            综合分析结果
        """
        result = {
            "industry_exposure": None,
            "factor_exposure": None,
            "concentration": None,
            "risk_metrics": None,
        }

        # 1. 行业暴露度
        if "industry" in positions.columns:
            result["industry_exposure"] = self.calculate_industry_exposure(positions)

        # 2. 因子暴露度
        if factor_data:
            result["factor_exposure"] = self.calculate_factor_exposure(
                positions, factor_data
            )

        # 3. 集中度
        result["concentration"] = self.calculate_concentration(positions)

        # 4. 风险指标
        result["risk_metrics"] = self.calculate_risk_metrics(
            returns, benchmark_returns
        )

        return result


# 全局组合分析服务实例
portfolio_analysis_service = PortfolioAnalysisService()
