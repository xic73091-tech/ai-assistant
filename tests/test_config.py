"""配置模块测试"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config, DEFAULT_CONFIG


class TestConfigInit:
    """测试配置初始化"""

    def test_default_config_when_no_file(self, tmp_config):
        """没有配置文件时使用默认配置"""
        config = Config(config_path=str(tmp_config))
        assert config.get("default_provider") == "openai"
        assert config.get("privacy.level") == "medium"
        assert config.config_path == tmp_config

    def test_config_dir_created(self, tmp_path):
        """配置目录自动创建"""
        config_path = tmp_path / "subdir" / "config.yaml"
        config = Config(config_path=str(config_path))
        assert config_path.parent.exists()

    def test_load_existing_config(self, tmp_config):
        """加载已存在的配置文件"""
        import yaml

        custom = {"default_provider": "claude", "privacy": {"level": "high"}}
        with open(tmp_config, "w", encoding="utf-8") as f:
            yaml.dump(custom, f)

        config = Config(config_path=str(tmp_config))
        assert config.get("default_provider") == "claude"
        assert config.get("privacy.level") == "high"

    def test_env_override_openai_key(self, tmp_config):
        """环境变量覆盖OpenAI API密钥"""
        config = Config(config_path=str(tmp_config))
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-123"}):
            config._apply_env_overrides()
            assert config.get("providers.openai.api_key") == "test-key-123"

    def test_env_override_claude_key(self, tmp_config):
        """环境变量覆盖Claude API密钥"""
        config = Config(config_path=str(tmp_config))
        with patch.dict("os.environ", {"CLAUDE_API_KEY": "claude-key-456"}):
            config._apply_env_overrides()
            assert config.get("providers.claude.api_key") == "claude-key-456"

    def test_env_override_default_provider(self, tmp_config):
        """环境变量覆盖默认提供商"""
        config = Config(config_path=str(tmp_config))
        with patch.dict("os.environ", {"AI_DEFAULT_PROVIDER": "claude"}):
            config._apply_env_overrides()
            assert config.get("default_provider") == "claude"


class TestConfigGetSet:
    """测试配置读写"""

    def test_get_simple_key(self, tmp_config):
        """获取简单键值"""
        config = Config(config_path=str(tmp_config))
        assert config.get("default_provider") in ("openai", "claude", "ollama")

    def test_get_nested_key(self, tmp_config):
        """获取嵌套键值"""
        config = Config(config_path=str(tmp_config))
        assert config.get("providers.openai.model") == "gpt-4o"

    def test_get_missing_key_returns_default(self, tmp_config):
        """获取不存在的键返回默认值"""
        config = Config(config_path=str(tmp_config))
        assert config.get("nonexistent.key", "fallback") == "fallback"

    def test_get_missing_key_returns_none(self, tmp_config):
        """获取不存在的键返回None"""
        config = Config(config_path=str(tmp_config))
        assert config.get("nonexistent.key") is None

    def test_set_simple_key(self, tmp_config):
        """设置简单键值"""
        config = Config(config_path=str(tmp_config))
        config.set("default_provider", "claude")
        assert config.get("default_provider") == "claude"

    def test_set_nested_key(self, tmp_config):
        """设置嵌套键值"""
        config = Config(config_path=str(tmp_config))
        config.set("providers.openai.model", "gpt-4o-mini")
        assert config.get("providers.openai.model") == "gpt-4o-mini"

    def test_set_persists_after_reload(self, tmp_config):
        """设置后重新加载仍然有效"""
        config = Config(config_path=str(tmp_config))
        config.set("cost.budget_alert", 25.0)

        config2 = Config(config_path=str(tmp_config))
        assert config2.get("cost.budget_alert") == 25.0


class TestProviderConfig:
    """测试提供商配置"""

    def test_get_provider_config_default(self, tmp_config):
        """获取默认提供商配置"""
        config = Config(config_path=str(tmp_config))
        pc = config.get_provider_config()
        assert "model" in pc

    def test_get_provider_config_specific(self, tmp_config):
        """获取指定提供商配置"""
        config = Config(config_path=str(tmp_config))
        pc = config.get_provider_config("claude")
        assert pc.get("model") == "claude-sonnet-4-20250514"

    def test_get_provider_config_unknown(self, tmp_config):
        """获取未知提供商配置返回空字典"""
        config = Config(config_path=str(tmp_config))
        pc = config.get_provider_config("unknown")
        assert pc == {}

    def test_set_get_api_key(self, tmp_config):
        """设置和获取API密钥"""
        config = Config(config_path=str(tmp_config))
        config.set_api_key("openai", "sk-test-key")
        assert config.get_api_key("openai") == "sk-test-key"

    def test_get_api_key_empty_by_default(self, tmp_config):
        """默认API密钥为空"""
        config = Config(config_path=str(tmp_config))
        assert config.get_api_key("openai") == ""

    def test_get_default_provider(self, tmp_config):
        """获取默认提供商"""
        config = Config(config_path=str(tmp_config))
        assert config.get_default_provider() in ("openai", "claude", "ollama")

    def test_set_default_provider(self, tmp_config):
        """设置默认提供商"""
        config = Config(config_path=str(tmp_config))
        config.set_default_provider("claude")
        assert config.get_default_provider() == "claude"

    def test_set_default_provider_invalid(self, tmp_config):
        """设置无效提供商抛出异常"""
        config = Config(config_path=str(tmp_config))
        with pytest.raises(ValueError, match="提供商必须是"):
            config.set_default_provider("invalid")


class TestPrivacyConfig:
    """测试隐私配置"""

    def test_get_privacy_level(self, tmp_config):
        """获取隐私级别"""
        config = Config(config_path=str(tmp_config))
        assert config.get_privacy_level() in ("low", "medium", "high")

    def test_set_privacy_level(self, tmp_config):
        """设置隐私级别"""
        config = Config(config_path=str(tmp_config))
        config.set_privacy_level("high")
        assert config.get_privacy_level() == "high"

    def test_set_privacy_level_invalid(self, tmp_config):
        """设置无效隐私级别抛出异常"""
        config = Config(config_path=str(tmp_config))
        with pytest.raises(ValueError, match="隐私级别必须是"):
            config.set_privacy_level("ultra")


class TestBudgetConfig:
    """测试预算配置"""

    def test_get_budget_alert(self, tmp_config):
        """获取预算警报阈值"""
        config = Config(config_path=str(tmp_config))
        assert config.get_budget_alert() == 10.0

    def test_set_budget_alert(self, tmp_config):
        """设置预算警报阈值"""
        config = Config(config_path=str(tmp_config))
        config.set_budget_alert(50.0)
        assert config.get_budget_alert() == 50.0


class TestStoragePath:
    """测试存储路径配置"""

    def test_get_storage_path(self, tmp_config):
        """获取存储路径"""
        config = Config(config_path=str(tmp_config))
        path = config.get_storage_path()
        assert isinstance(path, Path)


class TestConfigShow:
    """测试配置显示"""

    def test_show_hides_api_keys(self, tmp_config):
        """显示配置时隐藏API密钥"""
        config = Config(config_path=str(tmp_config))
        config.set_api_key("openai", "sk-1234567890abcdef")
        shown = config.show()
        assert shown["providers"]["openai"]["api_key"] == "***cdef"

    def test_show_no_key_when_empty(self, tmp_config):
        """API密钥为空时不做特殊处理"""
        config = Config(config_path=str(tmp_config))
        shown = config.show()
        assert shown["providers"]["openai"]["api_key"] == ""


class TestConfigReset:
    """测试配置重置"""

    def test_reset_restores_defaults(self, tmp_config):
        """重置恢复默认配置"""
        config = Config(config_path=str(tmp_config))
        config.set("default_provider", "claude")
        config.set("cost.budget_alert", 99.0)
        config.reset()

        assert config.get("default_provider") == "openai"
        assert config.get("cost.budget_alert") == 10.0
