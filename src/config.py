"""配置管理模块"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

# 默认配置
DEFAULT_CONFIG = {
    "providers": {
        "openai": {
            "api_key": "",
            "model": "gpt-4o",
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        "claude": {
            "api_key": "",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "temperature": 0.7,
        },
    },
    "default_provider": "openai",
    "privacy": {
        "level": "medium",  # low, medium, high
        "detect_sensitive": True,
        "local_storage_only": True,
    },
    "storage": {
        "path": "~/.ai-assistant/data",
        "max_history": 1000,
    },
    "cost": {
        "currency": "USD",
        "budget_alert": 10.0,
    },
}


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "~/.ai-assistant/config.yaml").expanduser()
        self.config_dir = self.config_path.parent
        self._config: dict[str, Any] = {}
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> None:
        """加载配置文件"""
        load_dotenv()

        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._save_config()

        # 环境变量覆盖
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        env_mapping = {
            "OPENAI_API_KEY": ("providers", "openai", "api_key"),
            "CLAUDE_API_KEY": ("providers", "claude", "api_key"),
            "OLLAMA_BASE_URL": ("providers", "ollama", "base_url"),
            "AI_DEFAULT_PROVIDER": ("default_provider",),
        }
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested(config_path, value)

    def _set_nested(self, path: tuple[str, ...], value: Any) -> None:
        """设置嵌套配置值"""
        config = self._config
        for key in path[:-1]:
            config = config.setdefault(key, {})
        config[path[-1]] = value

    def _save_config(self) -> None:
        """保存配置文件"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的路径"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的路径"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self._save_config()

    def get_provider_config(self, provider: Optional[str] = None) -> dict[str, Any]:
        """获取提供商配置"""
        provider = provider or self.get("default_provider", "openai")
        return self.get(f"providers.{provider}", {})

    def get_api_key(self, provider: str) -> str:
        """获取API密钥"""
        config = self.get_provider_config(provider)
        return config.get("api_key", "")

    def set_api_key(self, provider: str, api_key: str) -> None:
        """设置API密钥"""
        self.set(f"providers.{provider}.api_key", api_key)

    def get_privacy_level(self) -> str:
        """获取隐私保护级别"""
        return self.get("privacy.level", "medium")

    def set_privacy_level(self, level: str) -> None:
        """设置隐私保护级别"""
        if level not in ("low", "medium", "high"):
            raise ValueError("隐私级别必须是 low, medium 或 high")
        self.set("privacy.level", level)

    def get_storage_path(self) -> Path:
        """获取存储路径"""
        path = self.get("storage.path", "~/.ai-assistant/data")
        return Path(path).expanduser()

    def get_default_provider(self) -> str:
        """获取默认提供商"""
        return self.get("default_provider", "openai")

    def set_default_provider(self, provider: str) -> None:
        """设置默认提供商"""
        if provider not in ("openai", "claude", "ollama"):
            raise ValueError("提供商必须是 openai, claude 或 ollama")
        self.set("default_provider", provider)

    def get_budget_alert(self) -> float:
        """获取预算警报阈值"""
        return self.get("cost.budget_alert", 10.0)

    def set_budget_alert(self, amount: float) -> None:
        """设置预算警报阈值"""
        self.set("cost.budget_alert", amount)

    def reset(self) -> None:
        """重置为默认配置"""
        self._config = DEFAULT_CONFIG.copy()
        self._save_config()

    def show(self) -> dict[str, Any]:
        """显示当前配置（隐藏敏感信息）"""
        config = self._config.copy()
        # 隐藏API密钥
        for provider in config.get("providers", {}).values():
            if "api_key" in provider and provider["api_key"]:
                provider["api_key"] = "***" + provider["api_key"][-4:]
        return config


# 全局配置实例
config = Config()
