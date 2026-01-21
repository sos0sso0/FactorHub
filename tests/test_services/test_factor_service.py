"""
因子服务单元测试
"""

import pytest
import pandas as pd
import numpy as np

from backend.services.factor_service import FactorService
from backend.repositories import FactorRepository
from backend.models import Factor
from backend.core.exceptions import ValidationException


class TestFactorService:
    """因子服务测试类"""

    def test_init_system_factors(self, test_db, test_settings, sample_factor_config):
        """测试系统因子初始化"""
        # 使用 sample_factor_config 夹具创建的配置文件
        service = FactorService(config_path=sample_factor_config)

        # 初始化系统因子
        count = service.init_system_factors()

        # 验证
        assert count == 2
        repo = FactorRepository(test_db)
        factors = repo.find_all()
        assert len(factors) == 2
        assert factors[0].name == "test_factor_1"
        assert factors[1].source == "system"

    def test_get_all_factors(self, test_db):
        """测试获取所有因子"""
        repo = FactorRepository(test_db)

        # 添加测试因子
        factor1 = Factor(
            name="test_factor_1",
            formula="df['close'].pct_change()",
            description="测试因子1",
            source="user",
            category="custom",
        )
        factor2 = Factor(
            name="test_factor_2",
            formula="np.log(df['close'])",
            description="测试因子2",
            source="system",
            category="price",
        )
        repo.create(factor1)
        repo.create(factor2)

        # 测试获取所有因子
        service = FactorService()
        factors = service.get_all_factors()

        assert len(factors) == 2
        assert factors[0]["name"] == "test_factor_1"
        assert factors[1]["source"] == "system"

    def test_get_all_factors_with_filter(self, test_db):
        """测试带过滤条件获取因子"""
        repo = FactorRepository(test_db)

        # 添加测试因子
        factor1 = Factor(
            name="user_factor",
            formula="df['close']",
            description="用户因子",
            source="user",
            category="custom",
        )
        factor2 = Factor(
            name="system_factor",
            formula="df['open']",
            description="系统因子",
            source="system",
            category="price",
        )
        repo.create(factor1)
        repo.create(factor2)

        # 测试过滤
        service = FactorService()
        user_factors = service.get_all_factors(source="user")
        system_factors = service.get_all_factors(source="system")

        assert len(user_factors) == 1
        assert len(system_factors) == 1
        assert user_factors[0]["source"] == "user"

    def test_get_factor_stats(self, test_db):
        """测试获取因子统计"""
        repo = FactorRepository(test_db)

        # 添加测试因子
        for i in range(3):
            factor = Factor(
                name=f"factor_{i}",
                formula="df['close']",
                description=f"测试因子{i}",
                source="user" if i < 2 else "system",
                category="custom" if i < 2 else "price",
            )
            repo.create(factor)

        # 测试统计
        service = FactorService()
        stats = service.get_factor_stats()

        assert stats["total"] == 3
        assert stats["user_count"] == 2
        assert stats["system_count"] == 1
        assert stats["categories"]["custom"] == 2
        assert stats["categories"]["price"] == 1

    def test_add_factor_success(self, test_db):
        """测试成功添加因子"""
        service = FactorService()

        # 添加因子
        result = service.add_factor(
            name="new_factor",
            formula="df['close'].pct_change()",
            description="新因子",
            category="custom",
        )

        assert result is True

        # 验证
        repo = FactorRepository(test_db)
        factor = repo.find_by_name("new_factor")
        assert factor is not None
        assert factor.source == "user"
        assert factor.category == "custom"

    def test_add_factor_invalid_formula(self, test_db):
        """测试添加无效公式的因子"""
        service = FactorService()

        # 测试无效公式
        with pytest.raises(ValidationException):
            service.add_factor(
                name="invalid_factor",
                formula="invalid_function()",
                description="无效公式",
            )

    def test_update_factor(self, test_db):
        """测试更新因子"""
        repo = FactorRepository(test_db)

        # 创建测试因子
        factor = Factor(
            name="test_factor",
            formula="df['close']",
            description="原描述",
            source="user",
            category="custom",
        )
        created_factor = repo.create(factor)

        # 更新因子
        service = FactorService()
        result = service.update_factor(
            factor_id=created_factor.id,
            name="updated_factor",
            description="新描述",
        )

        assert result is True

        # 验证
        test_db.refresh(created_factor)
        assert created_factor.name == "updated_factor"
        assert created_factor.description == "新描述"

    def test_delete_factor(self, test_db):
        """测试删除因子"""
        repo = FactorRepository(test_db)

        # 创建测试因子
        factor = Factor(
            name="test_factor",
            formula="df['close']",
            description="测试",
            source="user",
            category="custom",
        )
        created_factor = repo.create(factor)

        # 删除因子
        service = FactorService()
        result = service.delete_factor(created_factor.id)

        assert result is True

        # 验证软删除
        deleted_factor = repo.find_by_id(created_factor.id)
        assert deleted_factor.is_active is False

    def test_validate_formula(self):
        """测试公式验证"""
        service = FactorService()

        # 有效公式
        result1 = service.validate_formula("df['close'].pct_change()")
        assert result1["valid"] is True
        assert result1["error"] is None

        # 无效公式
        result2 = service.validate_formula("invalid_function()")
        assert result2["valid"] is False
        assert result2["error"] is not None

    def test_compute_factors(self, test_db, sample_ohlcv_data):
        """测试因子计算"""
        repo = FactorRepository(test_db)

        # 创建测试因子
        factor = Factor(
            name="returns",
            formula="df['close'].pct_change()",
            description="收益率",
            source="system",
            category="price_return",
        )
        repo.create(factor)

        # 计算因子
        service = FactorService()
        result_df = service.compute_factors(sample_ohlcv_data, ["returns"])

        # 验证
        assert "returns" in result_df.columns
        assert len(result_df) == len(sample_ohlcv_data)
