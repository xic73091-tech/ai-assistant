"""共享测试夹具"""

import sys
import tempfile
from pathlib import Path

import pytest

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_db(tmp_path):
    """提供临时数据库路径"""
    db_path = tmp_path / "test.db"
    return db_path


@pytest.fixture
def tmp_config(tmp_path):
    """提供临时配置文件路径"""
    config_path = tmp_path / "config.yaml"
    return config_path


@pytest.fixture
def tmp_dir(tmp_path):
    """提供临时目录"""
    return tmp_path
