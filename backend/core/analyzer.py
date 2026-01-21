"""
因子分析器
使用 XGBoost 和 SHAP 进行因子有效性分析
"""

import shap
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class FactorAnalyzer:
    """因子分析器"""

    def __init__(self):
        self.model = None
        self.shap_values = None
        self.explainer = None
        self.feature_names = None
        self.scaler = StandardScaler()

    def prepare_features(
        self, df: pd.DataFrame, factor_names: List[str], window: int = 252
    ) -> pd.DataFrame:
        """
        准备特征数据

        Args:
            df: OHLCV 数据
            factor_names: 因子名称列表
            window: 滚动窗口大小

        Returns:
            包含特征的目标变量的 DataFrame
        """
        result_df = df.copy()

        # 计算未来收益率作为目标变量
        result_df["future_return"] = result_df["close"].pct_change(5).shift(-5)

        # 滚动窗口标准化
        for factor in factor_names:
            if factor in result_df.columns:
                # 计算滚动统计量
                rolling_mean = result_df[factor].rolling(window=window, min_periods=1).mean()
                rolling_std = result_df[factor].rolling(window=window, min_periods=1).std()

                # 标准化
                result_df[f"{factor}_std"] = (result_df[factor] - rolling_mean) / (
                    rolling_std + 1e-8
                )

        # 添加时间特征
        result_df["day_of_week"] = result_df.index.dayofweek
        result_df["month"] = result_df.index.month

        # 删除包含 NaN 的行
        result_df = result_df.dropna()

        return result_df

    def train_model(
        self,
        df: pd.DataFrame,
        feature_names: List[str],
        target_col: str = "future_return",
        test_size: float = 0.2,
    ) -> Dict:
        """
        训练 XGBoost 模型

        Returns:
            训练结果字典
        """
        try:
            # 准备特征和目标
            X = df[feature_names].values
            y = df[target_col].values

            # 分割训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )

            # 训练 XGBoost 模型
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )

            self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

            # 预测
            y_pred_train = self.model.predict(X_train)
            y_pred_test = self.model.predict(X_test)

            # 计算评估指标
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

            # 计算 SHAP 值
            try:
                self.explainer = shap.TreeExplainer(self.model)
                self.shap_values = self.explainer.shap_values(X_test)
            except Exception as e:
                logger.warning(f"SHAP 计算失败: {e}")

            self.feature_names = feature_names

            # 特征重要性（转换为 Python 原生类型）
            feature_importance = dict(
                zip(feature_names, [float(x) for x in self.model.feature_importances_])
            )
            sorted_importance = dict(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            )

            results = {
                "train_r2": float(train_r2),
                "test_r2": float(test_r2),
                "train_rmse": float(train_rmse),
                "test_rmse": float(test_rmse),
                "feature_importance": sorted_importance,
                "n_features": int(len(feature_names)),
                "n_samples": int(len(df)),
            }

            logger.info(f"模型训练完成: Test R² = {test_r2:.4f}")
            return results

        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            raise

    def calculate_ic(self, df: pd.DataFrame, factor_name: str) -> Dict:
        """
        计算因子 IC (Information Coefficient)

        Args:
            df: 包含因子和未来收益的数据
            factor_name: 因子名称

        Returns:
            IC 统计信息
        """
        try:
            # 计算 IC（相关系数）
            ic = df[factor_name].corr(df["future_return"])

            # 计算 IR (Information Ratio) = IC均值 / IC标准差
            # 这里简化为单期 IC
            ir = ic if not np.isnan(ic) else 0

            # 计算 IC 的统计显著性
            from scipy.stats import pearsonr

            corr, p_value = pearsonr(df[factor_name].dropna(), df["future_return"].dropna())

            return {
                "ic": float(ic) if not np.isnan(ic) else 0.0,
                "ir": float(ir) if not np.isnan(ir) else 0.0,
                "p_value": float(p_value) if not np.isnan(p_value) else 1.0,
                "abs_ic": float(abs(ic)) if not np.isnan(ic) else 0.0,
            }

        except Exception as e:
            logger.error(f"计算 IC 失败: {e}")
            return {"ic": 0.0, "ir": 0.0, "p_value": 1.0, "abs_ic": 0.0}

    def calculate_rolling_ic(
        self, df: pd.DataFrame, factor_name: str, window: int = 20
    ) -> pd.Series:
        """计算滚动 IC"""
        try:
            rolling_ic = (
                df[factor_name].rolling(window=window).corr(df["future_return"])
            )
            return rolling_ic
        except Exception as e:
            logger.error(f"计算滚动 IC 失败: {e}")
            return pd.Series()

    def get_shap_summary(self) -> Dict:
        """获取 SHAP 分析摘要"""
        if self.shap_values is None:
            return {}

        # 计算平均绝对 SHAP 值（转换为 Python 原生类型）
        mean_abs_shap = [float(x) for x in np.abs(self.shap_values).mean(axis=0)]

        feature_importance_shap = dict(
            zip(self.feature_names, mean_abs_shap)
        )
        sorted_shap = dict(
            sorted(feature_importance_shap.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "mean_abs_shap": sorted_shap,
            "shap_values_shape": list(self.shap_values.shape),  # 转换为列表
        }

    def generate_shap_force_plot_data(self, X_sample: np.ndarray) -> Dict:
        """生成 SHAP 力图数据（用于前端可视化）"""
        if self.explainer is None:
            return {}

        # 选择第一个样本
        shap_values = self.explainer.shap_values(X_sample[:1])

        return {
            "base_value": float(self.explainer.expected_value[0]),
            "shap_values": shap_values[0].tolist(),
            "feature_names": self.feature_names,
            "feature_values": X_sample[0].tolist(),
        }

    def calculate_monthly_ic(
        self, df: pd.DataFrame, factor_name: str
    ) -> pd.DataFrame:
        """计算月度 IC"""
        try:
            # 按月分组计算 IC
            monthly_ic = (
                df.groupby(df.index.to_period("M"))
                .apply(lambda x: x[factor_name].corr(x["future_return"]))
                .reset_index()
            )
            monthly_ic.columns = ["month", "ic"]
            monthly_ic["month"] = monthly_ic["month"].astype(str)

            return monthly_ic

        except Exception as e:
            logger.error(f"计算月度 IC 失败: {e}")
            return pd.DataFrame(columns=["month", "ic"])

    def save_results(self, results: Dict, save_path: Path):
        """保存分析结果"""
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化的格式
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = {
                    k: float(v) if isinstance(v, (np.integer, np.floating)) else v
                    for k, v in value.items()
                }
            else:
                serializable_results[key] = value

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)

        logger.info(f"结果已保存: {save_path}")
