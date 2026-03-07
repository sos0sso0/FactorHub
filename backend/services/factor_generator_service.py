"""
因子生成器服务 - 基于预置因子生成新因子
"""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import random
from itertools import combinations, product


class FactorGeneratorService:
    """因子生成器服务"""

    def __init__(self):
        # 可用的运算符
        self.operators = {
            "+": "加法",
            "-": "减法",
            "*": "乘法",
            "/": "除法",
        }

        # 可用的统计函数
        self.statistics = {
            "rank": "排名",
            "zscore": "Z-score标准化",
            "mean": "均值",
            "std": "标准差",
            "max": "最大值",
            "min": "最小值",
        }

        # 可用的技术指标
        self.indicators = {
            "SMA": "简单移动平均",
            "EMA": "指数移动平均",
            "RSI": "相对强弱指标",
            "MACD": "MACD",
        }

    def generate_binary_combinations(
        self,
        base_factors: List[str],
        max_depth: int = 3,
        max_combinations: int = 100
    ) -> List[str]:
        """
        生成二元运算组合因子

        Args:
            base_factors: 基础因子列表
            max_depth: 最大深度（嵌套层数）
            max_combinations: 最大组合数

        Returns:
            因子表达式列表
        """
        expressions = []

        if len(base_factors) < 2:
            return expressions

        # 生成深度1的组合
        for factor1, factor2 in combinations(base_factors, 2):
            for op in self.operators.keys():
                expr = f"({factor1} {op} {factor2})"
                expressions.append(expr)

        # 生成深度2的组合（如果需要）
        if max_depth >= 2 and len(base_factors) >= 3:
            for _ in range(min(max_combinations // 2, 50)):  # 限制数量
                # 随机选择3个因子
                selected = random.sample(base_factors, min(3, len(base_factors)))
                ops = random.sample(list(self.operators.keys()), 2)

                # 生成嵌套表达式
                expr = f"(({selected[0]} {ops[0]} {selected[1]}) {ops[1]} {selected[2]})"
                expressions.append(expr)

        # 生成深度3的组合（如果需要）
        if max_depth >= 3 and len(base_factors) >= 4:
            for _ in range(min(max_combinations // 4, 25)):  # 限制数量
                selected = random.sample(base_factors, min(4, len(base_factors)))
                ops = random.sample(list(self.operators.keys()), 3)

                expr = f"(({selected[0]} {ops[0]} {selected[1]}) {ops[1]} ({selected[2]} {ops[2]} {selected[3]}))"
                expressions.append(expr)

        return expressions[:max_combinations]

    def generate_statistical_combinations(
        self,
        base_factors: List[str],
        window_sizes: List[int] = [5, 10, 20, 60],
        max_combinations: int = 50
    ) -> List[str]:
        """
        生成统计函数组合因子

        Args:
            base_factors: 基础因子列表
            window_sizes: 窗口大小列表
            max_combinations: 最大组合数

        Returns:
            因子表达式列表
        """
        expressions = []

        for factor in base_factors:
            for stat_func in self.statistics.keys():
                if stat_func in ["mean", "std", "max", "min"]:
                    # 这些函数需要窗口参数
                    for window in window_sizes:
                        expr = f"{stat_func}({factor}, {window})"
                        expressions.append(expr)
                else:
                    # rank和zscore不需要窗口
                    expr = f"{stat_func}({factor})"
                    expressions.append(expr)

        return expressions[:max_combinations]

    def generate_indicator_combinations(
        self,
        base_factors: List[str],
        price_column: str = "close",
        max_combinations: int = 30
    ) -> List[str]:
        """
        生成技术指标组合因子

        Args:
            base_factors: 基础因子列表
            price_column: 价格列名
            max_combinations: 最大组合数

        Returns:
            因子表达式列表
        """
        expressions = []

        # 为每个基础因子生成与技术指标的组合
        for factor in base_factors:
            for indicator in self.indicators.keys():
                if indicator == "SMA":
                    for window in [5, 10, 20, 60]:
                        expr = f"({factor} / SMA({price_column}, {window}))"
                        expressions.append(expr)
                        expr = f"({factor} - SMA({price_column}, {window}))"
                        expressions.append(expr)
                elif indicator == "EMA":
                    for window in [5, 10, 20, 60]:
                        expr = f"({factor} / EMA({price_column}, {window}))"
                        expressions.append(expr)
                elif indicator == "RSI":
                    expr = f"({factor} * RSI({price_column}, 14))"
                    expressions.append(expr)
                elif indicator == "MACD":
                    expr = f"({factor} * MACD({price_column}))"
                    expressions.append(expr)

        return expressions[:max_combinations]

    def generate_hybrid_factors(
        self,
        base_factors: List[str],
        n_factors: int = 100
    ) -> List[Dict]:
        """
        生成混合因子（结合多种方法）

        Args:
            base_factors: 基础因子列表
            n_factors: 生成因子数量

        Returns:
            因子字典列表，包含表达式和元数据
        """
        factors = []

        # 1. 二元运算组合（40%）
        n_binary = int(n_factors * 0.4)
        binary_exprs = self.generate_binary_combinations(
            base_factors,
            max_combinations=n_binary
        )

        for expr in binary_exprs:
            factors.append({
                "expression": expr,
                "type": "binary_operation",
                "complexity": "medium",
            })

        # 2. 统计函数组合（30%）
        n_statistical = int(n_factors * 0.3)
        stat_exprs = self.generate_statistical_combinations(
            base_factors,
            max_combinations=n_statistical
        )

        for expr in stat_exprs:
            factors.append({
                "expression": expr,
                "type": "statistical",
                "complexity": "low",
            })

        # 3. 技术指标组合（20%）
        n_indicator = int(n_factors * 0.2)
        indicator_exprs = self.generate_indicator_combinations(
            base_factors,
            max_combinations=n_indicator
        )

        for expr in indicator_exprs:
            factors.append({
                "expression": expr,
                "type": "indicator_based",
                "complexity": "high",
            })

        # 4. 随机组合（10%）
        n_random = n_factors - len(factors)

        for _ in range(n_random):
            if len(base_factors) >= 2:
                factor1, factor2 = random.sample(base_factors, 2)
                op = random.choice(list(self.operators.keys()))

                # 随机添加统计函数
                if random.random() < 0.3:
                    stat_func = random.choice(list(self.statistics.keys()))
                    if stat_func in ["mean", "std", "max", "min"]:
                        window = random.choice([5, 10, 20])
                        expr = f"{stat_func}({factor1} {op} {factor2}, {window})"
                    else:
                        expr = f"{stat_func}({factor1} {op} {factor2})"
                else:
                    expr = f"({factor1} {op} {factor2})"

                factors.append({
                    "expression": expr,
                    "type": "random_hybrid",
                    "complexity": random.choice(["low", "medium", "high"]),
                })

        # 打乱顺序
        random.shuffle(factors)

        return factors[:n_factors]

    def compile_expression_to_code(
        self,
        expression: str,
        data_column: str = "close"
    ) -> str:
        """
        将因子表达式编译为可执行代码

        Args:
            expression: 因子表达式
            data_column: 数据列名

        Returns:
            可执行的Python代码
        """
        # 替换函数为实际实现
        code = expression

        # 替换统计函数
        code = code.replace(
            "rank(",
            f".rank(pct=True).rolling(252, min_periods=1)."
        )
        code = code.replace("zscore(", "((")
        code = code.replace(
            "mean(",
            f".rolling(window=252, min_periods=1)."
        )
        code = code.replace(
            "std(",
            f".rolling(window=252, min_periods=1)."
        )

        # 替换技术指标
        code = code.replace("SMA(", "talib.SMA(")
        code = code.replace("EMA(", "talib.EMA(")
        code = code.replace("RSI(", "talib.RSI(")
        code = code.replace("MACD(", "talib.MACD(")

        # 包装成完整的代码
        full_code = f"""
import talib
import pandas as pd
import numpy as np

def calculate_factor(df):
    '''计算因子: {expression}'''

    # 确保有必要的列
    if '{data_column}' not in df.columns:
        raise ValueError("数据中缺少 '{data_column}' 列")

    # 计算因子
    try:
        factor = {code}

        # 处理zscore特殊情况
        if isinstance(factor, pd.Series):
            factor = (factor - factor.mean()) / (factor.std() + 1e-8)

        return factor
    except Exception as e:
        print(f"计算因子时出错: {{e}}")
        return pd.Series(index=df.index, dtype=float)
"""

        return full_code

    def validate_expression(self, expression: str) -> tuple[bool, str]:
        """
        验证因子表达式是否有效

        Args:
            expression: 因子表达式

        Returns:
            (是否有效, 错误信息)
        """
        # 基本语法检查
        if not expression or expression.strip() == "":
            return False, "表达式为空"

        # 检查括号匹配
        if expression.count("(") != expression.count(")"):
            return False, "括号不匹配"

        # 检查是否有非法字符
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/()., _"
        )
        for char in expression:
            if char not in allowed_chars:
                return False, f"包含非法字符: {char}"

        # 检查是否有运算符
        has_operator = any(op in expression for op in ["+", "-", "*", "/"])
        has_function = any(func in expression for func in self.statistics.keys())

        if not (has_operator or has_function):
            return False, "表达式缺少运算符或函数"

        return True, ""

    def parse_expression(self, expression: str) -> Dict:
        """
        解析因子表达式，提取结构

        Args:
            expression: 因子表达式

        Returns:
            解析后的结构信息
        """
        structure = {
            "expression": expression,
            "components": [],
            "operators": [],
            "functions": [],
            "depth": 0,
        }

        # 提取运算符
        for op in self.operators.keys():
            if op in expression:
                structure["operators"].append(op)

        # 提取函数
        for func in self.statistics.keys():
            if f"{func}(" in expression:
                structure["functions"].append(func)

        for func in self.indicators.keys():
            if f"{func}(" in expression:
                structure["functions"].append(func)

        # 计算深度（括号嵌套层数）
        max_depth = 0
        current_depth = 0
        for char in expression:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1

        structure["depth"] = max_depth

        return structure


# 全局因子生成器服务实例
factor_generator_service = FactorGeneratorService()
