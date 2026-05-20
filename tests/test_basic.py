"""基本功能测试 - 验证各模块核心功能可用"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_assistant.config import Config
from ai_assistant.privacy import PrivacyProtector
from ai_assistant.templates.manager import TemplateManager
from ai_assistant.storage import Storage


class TestConfig:
    """配置模块基本测试"""

    def test_config_loads(self, tmp_path):
        """配置能正常加载"""
        config = Config(config_path=str(tmp_path / "config.yaml"))
        assert config.get("default_provider") in ("openai", "claude", "ollama")
        assert config.get_privacy_level() in ("low", "medium", "high")

    def test_config_get_set(self, tmp_path):
        """配置读写"""
        config = Config(config_path=str(tmp_path / "config.yaml"))
        config.set("cost.budget_alert", 25.0)
        assert config.get("cost.budget_alert") == 25.0

    def test_config_provider_config(self, tmp_path):
        """获取提供商配置"""
        config = Config(config_path=str(tmp_path / "config.yaml"))
        pc = config.get_provider_config("openai")
        assert "model" in pc

    def test_config_privacy_level_validation(self, tmp_path):
        """隐私级别校验"""
        config = Config(config_path=str(tmp_path / "config.yaml"))
        with pytest.raises(ValueError):
            config.set_privacy_level("invalid")

    def test_config_provider_validation(self, tmp_path):
        """提供商校验"""
        config = Config(config_path=str(tmp_path / "config.yaml"))
        with pytest.raises(ValueError):
            config.set_default_provider("invalid")

    def test_config_show_hides_keys(self, tmp_path):
        """显示配置时隐藏密钥"""
        config = Config(config_path=str(tmp_path / "config.yaml"))
        config.set_api_key("openai", "sk-abcdefghijklmnop")
        shown = config.show()
        assert "sk-abcdefghijklmnop" not in str(shown)
        assert "***" in shown["providers"]["openai"]["api_key"]


class TestPrivacy:
    """隐私保护模块基本测试"""

    def test_detect_phone(self):
        """检测手机号"""
        protector = PrivacyProtector(level="medium")
        text = "我的手机号是13812345678"
        results = protector.detect(text)
        phone_results = [r for r in results if r.type == "phone"]
        assert len(phone_results) == 1

    def test_detect_id_card(self):
        """检测身份证号"""
        protector = PrivacyProtector(level="medium")
        text = "身份证号110101199001011234"
        results = protector.detect(text)
        id_results = [r for r in results if r.type == "id_card"]
        assert len(id_results) == 1

    def test_mask_phone(self):
        """手机号脱敏"""
        protector = PrivacyProtector(level="medium")
        masked = protector.mask("手机号13812345678")
        assert "138****5678" in masked
        assert "13812345678" not in masked

    def test_mask_preserves_context(self):
        """脱敏保留上下文"""
        protector = PrivacyProtector(level="medium")
        masked = protector.mask("请拨打13812345678联系")
        assert "请拨打" in masked
        assert "联系" in masked

    def test_level_affects_detection(self):
        """隐私级别影响检测范围"""
        low = PrivacyProtector(level="low")
        high = PrivacyProtector(level="high")
        # high应该有更多检测项
        assert len(high.enabled_levels) > len(low.enabled_levels)


class TestTemplates:
    """模板模块基本测试"""

    def test_list_templates(self):
        """列出模板"""
        manager = TemplateManager()
        templates = manager.list_templates()
        assert len(templates) > 0

    def test_get_template(self):
        """获取模板"""
        manager = TemplateManager()
        template = manager.get_template("code-review")
        assert template is not None
        assert template.description == "代码审查助手"

    def test_render_template(self):
        """渲染模板"""
        manager = TemplateManager()
        template = manager.get_template("code-review")
        rendered = template.render(
            language="python",
            code="print('hello')",
            focus="代码质量",
        )
        assert "python" in rendered
        assert "print('hello')" in rendered
        assert "代码质量" in rendered

    def test_get_categories(self):
        """获取分类"""
        manager = TemplateManager()
        categories = manager.get_categories()
        assert "code" in categories
        assert "writing" in categories

    def test_search_templates(self):
        """搜索模板"""
        manager = TemplateManager()
        results = manager.search_templates("code")
        assert len(results) >= 1

    def test_nonexistent_template(self):
        """不存在的模板返回None"""
        manager = TemplateManager()
        assert manager.get_template("nonexistent") is None


class TestStorage:
    """存储模块基本测试"""

    def test_create_conversation(self, tmp_db):
        """创建对话"""
        storage = Storage(tmp_db)
        conv_id = storage.create_conversation("测试对话", "openai", "gpt-4o")
        assert conv_id > 0

    def test_add_message(self, tmp_db):
        """添加消息"""
        storage = Storage(tmp_db)
        conv_id = storage.create_conversation("测试", "openai", "gpt-4o")
        msg_id = storage.add_message(conv_id, "user", "你好", 10, 0.001)
        assert msg_id > 0

    def test_get_conversation(self, tmp_db):
        """获取对话"""
        storage = Storage(tmp_db)
        conv_id = storage.create_conversation("测试对话", "openai", "gpt-4o")
        conv = storage.get_conversation(conv_id)
        assert conv is not None
        assert conv["title"] == "测试对话"

    def test_get_messages(self, tmp_db):
        """获取消息"""
        storage = Storage(tmp_db)
        conv_id = storage.create_conversation("测试", "openai", "gpt-4o")
        storage.add_message(conv_id, "user", "你好")
        messages = storage.get_conversation_messages(conv_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "你好"

    def test_cost_records(self, tmp_db):
        """成本记录"""
        storage = Storage(tmp_db)
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        stats = storage.get_cost_stats()
        assert stats["total_cost"] == 0.01

    def test_delete_conversation(self, tmp_db):
        """删除对话"""
        storage = Storage(tmp_db)
        conv_id = storage.create_conversation("待删除", "openai", "gpt-4o")
        storage.delete_conversation(conv_id)
        assert storage.get_conversation(conv_id) is None

    def test_list_conversations(self, tmp_db):
        """列出对话"""
        storage = Storage(tmp_db)
        storage.create_conversation("对话1", "openai", "gpt-4o")
        storage.create_conversation("对话2", "claude", "claude-sonnet-4-20250514")
        conversations = storage.list_conversations()
        assert len(conversations) == 2


class TestProviderBase:
    """提供商基类基本测试"""

    def test_message_dataclass(self):
        """Message数据类"""
        from ai_assistant.providers.base import Message
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_usage_dataclass(self):
        """Usage数据类"""
        from ai_assistant.providers.base import Usage
        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.total_tokens == 30

    def test_chat_response_dataclass(self):
        """ChatResponse数据类"""
        from ai_assistant.providers.base import ChatResponse, Usage
        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        resp = ChatResponse(
            content="hi", model="gpt-4o", usage=usage, provider="openai"
        )
        assert resp.content == "hi"
        assert resp.finish_reason is None

    def test_cost_calculation(self):
        """成本计算"""
        from ai_assistant.providers.base import BaseProvider, Usage
        usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000)
        cost = BaseProvider.calculate_cost(usage, "gpt-4o")
        assert cost > 0
