"""
API 客户端模块
封装与后端 API 的通信
"""

import requests
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """API 客户端类"""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """
        执行 API 请求

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点
            data: 请求体数据
            params: 查询参数

        Returns:
            响应 JSON 数据，失败返回 None
        """
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=self.timeout)
            elif method == "DELETE":
                response = requests.delete(url, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"API 请求超时: {method} {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"API 连接失败: {method} {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {method} {url} - {str(e)}")
            return None

    # 健康检查
    def health_check(self) -> Optional[Dict]:
        """健康检查"""
        return self._make_request("GET", "/health")

    # 因子管理 API
    def get_factors(self, source: Optional[str] = None) -> Optional[Dict]:
        """获取因子列表"""
        return self._make_request("GET", "/api/factors", params={"source": source})

    def get_factor_stats(self) -> Optional[Dict]:
        """获取因子统计"""
        return self._make_request("GET", "/api/factors/stats")

    def create_factor(
        self, name: str, formula: str, description: str, category: str
    ) -> Optional[Dict]:
        """创建因子"""
        return self._make_request(
            "POST",
            "/api/factors",
            data={
                "name": name,
                "formula": formula,
                "description": description,
                "category": category,
            },
        )

    def update_factor(
        self,
        factor_id: int,
        name: Optional[str] = None,
        formula: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[Dict]:
        """更新因子"""
        data = {}
        if name is not None:
            data["name"] = name
        if formula is not None:
            data["formula"] = formula
        if description is not None:
            data["description"] = description
        if category is not None:
            data["category"] = category

        return self._make_request("PUT", f"/api/factors/{factor_id}", data=data)

    def delete_factor(self, factor_id: int) -> Optional[Dict]:
        """删除因子"""
        return self._make_request("DELETE", f"/api/factors/{factor_id}")

    def validate_formula(self, formula: str) -> Optional[Dict]:
        """验证因子公式"""
        return self._make_request("POST", "/api/factors/validate", data={"formula": formula})

    # 数据获取 API
    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[Dict]:
        """获取市场数据"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._make_request("GET", f"/api/data/{symbol}", params=params)

    # 分析 API
    def run_analysis(
        self,
        symbols: List[str],
        factors: List[str],
        start_date: str,
        end_date: str,
        mode: str = "pool",
    ) -> Optional[Dict]:
        """执行因子分析"""
        return self._make_request(
            "POST",
            "/api/analysis",
            data={
                "symbols": symbols,
                "factors": factors,
                "start_date": start_date,
                "end_date": end_date,
                "mode": mode,
            },
        )

    def compute_factors(
        self, symbol: str, factors: List[str]
    ) -> Optional[Dict]:
        """计算因子值"""
        factors_str = ",".join(factors)
        return self._make_request("GET", f"/api/analysis/factors/{symbol}", params={"factors": factors_str})


# 全局 API 客户端实例
api_client = APIClient()
