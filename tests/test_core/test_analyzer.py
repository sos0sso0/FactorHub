"""
因子分析器单元测试
"""

import pytest
import pandas as pd
import numpy as np

from backend.core.analyzer import FactorAnalyzer


class TestFactorAnalyzer:
    """因子分析器测试类"""

    def test_prepare_features(self, sample_ohlcv_data):
        """测试特征准备"""
        analyzer = FactorAnalyzer()

        # 添加测试因子列
        df = sample_ohlcv_data.copy()
        df["returns"] = df["close"].pct_change()

        # 准备特征
        result_df = analyzer.prepare_features(df, ["returns"], window=20)

        # 验证
        assert "future_return" in result_df.columns
        assert "returns_std" in result_df.columns
        assert "day_of_week" in result_df.columns
        assert "month" in result_df.columns
        assert len(result_df) < len(df)  # 由于 dropna

    def test_train_model(self, sample_ohlcv_data):
        """测试模型训练"""
        analyzer = FactorAnalyzer()

        # 准备数据
        df = sample_ohlcv_data.copy()
        df["returns"] = df["close"].pct_change()
        df = analyzer.prepare_features(df, ["returns"], window=20)

        # 训练模型
        feature_names = ["returns_std"]
        results = analyzer.train_model(df, feature_names)

        # 验证
        assert "train_r2" in results
        assert "test_r2" in results
        assert "train_rmse" in results
        assert "test_rmse" in results
        assert "feature_importance" in results
        assert results["n_features"] == 1
        assert analyzer.model is not None

    def test_calculate_ic(self, sample_ohlcv_data):
        """测试 IC 计算"""
        analyzer = FactorAnalyzer()

        # 准备数据
        df = sample_ohlcv_data.copy()
        df["returns"] = df["close"].pct_change()
        df = analyzer.prepare_features(df, ["returns"], window=20)

        # 计算 IC
        ic_result = analyzer.calculate_ic(df, "returns_std")

        # 验证
        assert "ic" in ic_result
        assert "ir" in ic_result
        assert "p_value" in ic_result
        assert "abs_ic" in ic_result
        assert -1 <= ic_result["ic"] <= 1

    def test_get_shap_summary(self, sample_ohlcv_data):
        """测试 SHAP 摘要"""
        analyzer = FactorAnalyzer()

        # 准备数据并训练
        df = sample_ohlcv_data.copy()
        df["returns"] = df["close"].pct_change()
        df = analyzer.prepare_features(df, ["returns"], window=20)

        feature_names = ["returns_std"]
        analyzer.train_model(df, feature_names)

        # 获取 SHAP 摘要
        shap_summary = analyzer.get_shap_summary()

        # 验证
        assert "mean_abs_shap" in shap_summary
        assert "shap_values_shape" in shap_summary
        assert len(shap_summary["mean_abs_shap"]) == 1

    def test_calculate_rolling_ic(self, sample_ohlcv_data):
        """测试滚动 IC 计算"""
        analyzer = FactorAnalyzer()

        # 准备数据
        df = sample_ohlcv_data.copy()
        df["returns"] = df["close"].pct_change()
        df = analyzer.prepare_features(df, ["returns"], window=20)

        # 计算滚动 IC
        rolling_ic = analyzer.calculate_rolling_ic(df, "returns_std", window=10)

        # 验证
        assert isinstance(rolling_ic, pd.Series)
        assert len(rolling_ic) > 0

    def test_calculate_monthly_ic(self, sample_ohlcv_data):
        """测试月度 IC 计算"""
        analyzer = FactorAnalyzer()

        # 准备数据
        df = sample_ohlcv_data.copy()
        df["returns"] = df["close"].pct_change()
        df = analyzer.prepare_features(df, ["returns"], window=20)

        # 计算月度 IC
        monthly_ic = analyzer.calculate_monthly_ic(df, "returns_std")

        # 验证
        assert isinstance(monthly_ic, pd.DataFrame)
        assert "month" in monthly_ic.columns
        assert "ic" in monthly_ic.columns
