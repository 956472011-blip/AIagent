"""Pytest 配置文件。

企业级测试配置:
    - fixtures: 共享测试数据
    - 环境变量: 测试环境配置
    - 数据库: 测试数据库初始化
"""
import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到 path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def test_env():
    """设置测试环境变量。"""
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["DASHSCOPE_API_KEY"] = "test-key"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    yield
    # 清理测试数据库
    test_db = ROOT / "test.db"
    if test_db.exists():
        test_db.unlink()


@pytest.fixture
def mock_user():
    """模拟用户数据。"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
    }
