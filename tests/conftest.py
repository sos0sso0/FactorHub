"""
pytest 配置文件
定义测试夹具和共享测试工具
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, close_all_sessions

from backend.models import Base


@pytest.fixture(scope="function")
def temp_dir():
    """临时目录夹具"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 清理
    try:
        if temp_path.exists():
            shutil.rmtree(temp_path)
    except PermissionError:
        # Windows 下文件可能被锁定，跳过删除
        pass


@pytest.fixture(scope="function")
def test_settings(temp_dir):
    """测试配置夹具"""
    from backend.core.settings import Settings

    # 使用内存数据库
    settings = Settings(
        BASE_DIR=temp_dir,
        DATABASE_URL="sqlite:///:memory:",
        DATA_DIR=temp_dir / "data",
        CACHE_DIR=temp_dir / "cache",
        LOGS_DIR=temp_dir / "logs",
        CONFIG_DIR=temp_dir / "config",
        AKSHARE_CACHE_DIR=temp_dir / "cache" / "akshare",
    )

    # 创建目录
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "data").mkdir(parents=True, exist_ok=True)
    (temp_dir / "cache").mkdir(parents=True, exist_ok=True)
    (temp_dir / "logs").mkdir(parents=True, exist_ok=True)
    (temp_dir / "config").mkdir(parents=True, exist_ok=True)

    return settings


@pytest.fixture(scope="function")
def test_db(test_settings):
    """测试数据库夹具"""
    # 创建内存数据库引擎
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 关闭所有会话
        close_all_sessions()
        # 清理
        engine.dispose()


@pytest.fixture(scope="function")
def sample_ohlcv_data():
    """示例 OHLCV 数据夹具"""
    import pandas as pd
    import numpy as np
    from datetime import datetime

    # 生成 100 天的测试数据
    dates = pd.date_range(start=datetime(2024, 1, 1), periods=100, freq="D")

    np.random.seed(42)
    base_price = 50000
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            "high": prices * (1 + np.random.uniform(0, 0.02, 100)),
            "low": prices * (1 - np.random.uniform(0, 0.02, 100)),
            "close": prices,
            "volume": np.random.randint(10000, 100000, 100),
        },
        index=dates,
    )

    return df


@pytest.fixture(scope="function")
def sample_factor_config(test_settings):
    """创建测试因子配置文件"""
    import yaml

    factor_config_path = test_settings.CONFIG_DIR / "factors.yaml"
    test_config = {
        "price_return_factors": [
            {
                "name": "test_factor_1",
                "formula": "df['close'].pct_change()",
                "description": "测试因子1",
            },
            {
                "name": "test_factor_2",
                "formula": "np.log(df['close'] / df['close'].shift(1))",
                "description": "测试因子2",
            },
        ]
    }

    with open(factor_config_path, "w", encoding="utf-8") as f:
        yaml.dump(test_config, f, allow_unicode=True)

    return factor_config_path
