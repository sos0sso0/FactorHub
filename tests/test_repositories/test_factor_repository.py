"""
因子仓储单元测试
"""

import pytest

from backend.repositories import FactorRepository
from backend.models import Factor
from backend.core.exceptions import NotFoundException, DataAccessException


class TestFactorRepository:
    """因子仓储测试类"""

    def test_create_factor_success(self, test_db):
        """测试成功创建因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="test_factor",
            formula="df['close'].pct_change()",
            description="测试因子",
            source="user",
            category="custom",
        )

        result = repo.create(factor)

        assert result.id is not None
        assert result.name == "test_factor"
        assert result.source == "user"

    def test_create_duplicate_factor(self, test_db):
        """测试创建重复因子"""
        repo = FactorRepository(test_db)

        factor1 = Factor(
            name="duplicate_factor",
            formula="df['close']",
            description="因子1",
            source="user",
            category="custom",
        )
        repo.create(factor1)

        # 尝试创建同名因子
        factor2 = Factor(
            name="duplicate_factor",
            formula="df['open']",
            description="因子2",
            source="user",
            category="custom",
        )

        with pytest.raises(DataAccessException, match="已存在"):
            repo.create(factor2)

    def test_find_by_id(self, test_db):
        """测试根据 ID 查找因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="test_factor",
            formula="df['close']",
            description="测试",
            source="system",
            category="price",
        )
        created = repo.create(factor)

        # 查找
        found = repo.find_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == "test_factor"

    def test_find_by_name(self, test_db):
        """测试根据名称查找因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="named_factor",
            formula="df['close']",
            description="测试",
            source="user",
            category="custom",
        )
        repo.create(factor)

        # 查找
        found = repo.find_by_name("named_factor")

        assert found is not None
        assert found.name == "named_factor"

    def test_find_all(self, test_db):
        """测试查找所有因子"""
        repo = FactorRepository(test_db)

        # 创建多个因子
        for i in range(3):
            factor = Factor(
                name=f"factor_{i}",
                formula="df['close']",
                description=f"因子{i}",
                source="user",
                category="custom",
            )
            repo.create(factor)

        # 查找所有
        factors = repo.find_all()

        assert len(factors) == 3

    def test_find_all_with_filter(self, test_db):
        """测试带过滤条件的查找"""
        repo = FactorRepository(test_db)

        # 创建不同来源的因子
        user_factor = Factor(
            name="user_factor",
            formula="df['close']",
            description="用户因子",
            source="user",
            category="custom",
        )
        system_factor = Factor(
            name="system_factor",
            formula="df['open']",
            description="系统因子",
            source="system",
            category="price",
        )
        repo.create(user_factor)
        repo.create(system_factor)

        # 测试过滤
        user_factors = repo.find_all(source="user")
        system_factors = repo.find_all(source="system")

        assert len(user_factors) == 1
        assert len(system_factors) == 1
        assert user_factors[0].source == "user"

    def test_get_stats(self, test_db):
        """测试获取统计信息"""
        repo = FactorRepository(test_db)

        # 创建测试数据
        for i in range(5):
            factor = Factor(
                name=f"factor_{i}",
                formula="df['close']",
                description=f"因子{i}",
                source="user" if i < 3 else "system",
                category="custom" if i < 2 else "price",
            )
            repo.create(factor)

        # 获取统计
        stats = repo.get_stats()

        assert stats["total"] == 5
        assert stats["user_count"] == 3
        assert stats["system_count"] == 2

    def test_update_factor_success(self, test_db):
        """测试成功更新因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="original_name",
            formula="df['close']",
            description="原描述",
            source="user",
            category="custom",
        )
        created = repo.create(factor)

        # 更新
        updated = repo.update(
            factor_id=created.id,
            name="updated_name",
            description="新描述",
        )

        assert updated.name == "updated_name"
        assert updated.description == "新描述"

    def test_update_system_factor_forbidden(self, test_db):
        """测试不允许修改系统因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="system_factor",
            formula="df['close']",
            description="系统因子",
            source="system",
            category="price",
        )
        created = repo.create(factor)

        # 尝试修改系统因子
        with pytest.raises(DataAccessException, match="不可修改"):
            repo.update(factor_id=created.id, name="new_name")

    def test_delete_factor_success(self, test_db):
        """测试成功删除因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="user_factor",
            formula="df['close']",
            description="用户因子",
            source="user",
            category="custom",
        )
        created = repo.create(factor)

        # 删除
        result = repo.delete(created.id)

        assert result is True

        # 验证软删除
        deleted = repo.find_by_id(created.id)
        assert deleted.is_active is False

    def test_delete_system_factor_forbidden(self, test_db):
        """测试不允许删除系统因子"""
        repo = FactorRepository(test_db)

        factor = Factor(
            name="system_factor",
            formula="df['close']",
            description="系统因子",
            source="system",
            category="price",
        )
        created = repo.create(factor)

        # 尝试删除系统因子
        with pytest.raises(DataAccessException, match="不可删除"):
            repo.delete(created.id)
