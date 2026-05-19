"""AI提供商接口测试（使用mock避免实际API调用）"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.base import BaseProvider, ChatResponse, Message, Usage


# ========== 基础数据类测试 ==========


class TestMessage:
    """测试Message数据类"""

    def test_message_creation(self):
        """创建消息"""
        msg = Message(role="user", content="你好")
        assert msg.role == "user"
        assert msg.content == "你好"

    def test_message_roles(self):
        """不同角色消息"""
        for role in ("user", "assistant", "system"):
            msg = Message(role=role, content="test")
            assert msg.role == role


class TestUsage:
    """测试Usage数据类"""

    def test_usage_defaults(self):
        """默认值"""
        usage = Usage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_usage_custom_values(self):
        """自定义值"""
        usage = Usage(prompt_tokens=100, completion_tokens=200, total_tokens=300)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 200
        assert usage.total_tokens == 300


class TestChatResponse:
    """测试ChatResponse数据类"""

    def test_chat_response_creation(self):
        """创建聊天响应"""
        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        resp = ChatResponse(
            content="你好！",
            model="gpt-4o",
            usage=usage,
            provider="openai",
            finish_reason="stop",
        )
        assert resp.content == "你好！"
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"
        assert resp.finish_reason == "stop"
        assert resp.usage.total_tokens == 30

    def test_chat_response_optional_finish_reason(self):
        """finish_reason可选"""
        usage = Usage()
        resp = ChatResponse(content="", model="m", usage=usage, provider="p")
        assert resp.finish_reason is None


# ========== BaseProvider测试 ==========


class TestBaseProviderHelpers:
    """测试BaseProvider辅助方法"""

    def _make_provider(self, config=None):
        """创建一个具体的Provider实例用于测试"""

        class ConcreteProvider(BaseProvider):
            async def chat(self, messages, model=None, temperature=None, max_tokens=None):
                pass

            async def chat_stream(self, messages, model=None, temperature=None, max_tokens=None):
                yield ""

        return ConcreteProvider(config or {"model": "test-model", "temperature": 0.5, "max_tokens": 2048})

    def test_get_model_from_config(self):
        """从配置获取模型"""
        p = self._make_provider({"model": "gpt-4o"})
        assert p.get_model() == "gpt-4o"

    def test_get_model_override(self):
        """覆盖模型"""
        p = self._make_provider({"model": "gpt-4o"})
        assert p.get_model("claude-sonnet-4-20250514") == "claude-sonnet-4-20250514"

    def test_get_temperature_from_config(self):
        """从配置获取温度"""
        p = self._make_provider({"temperature": 0.3})
        assert p.get_temperature() == 0.3

    def test_get_temperature_override(self):
        """覆盖温度"""
        p = self._make_provider({"temperature": 0.3})
        assert p.get_temperature(0.9) == 0.9

    def test_get_temperature_default(self):
        """温度默认值"""
        p = self._make_provider({})
        assert p.get_temperature() == 0.7

    def test_get_max_tokens_from_config(self):
        """从配置获取max_tokens"""
        p = self._make_provider({"max_tokens": 8192})
        assert p.get_max_tokens() == 8192

    def test_get_max_tokens_override(self):
        """覆盖max_tokens"""
        p = self._make_provider({"max_tokens": 8192})
        assert p.get_max_tokens(1024) == 1024

    def test_get_max_tokens_default(self):
        """max_tokens默认值"""
        p = self._make_provider({})
        assert p.get_max_tokens() == 4096

    def test_validate_messages_valid(self):
        """验证有效消息"""
        p = self._make_provider()
        messages = [Message(role="user", content="hello")]
        p.validate_messages(messages)  # 不应抛异常

    def test_validate_messages_empty(self):
        """空消息列表抛异常"""
        p = self._make_provider()
        with pytest.raises(ValueError, match="消息列表不能为空"):
            p.validate_messages([])

    def test_validate_messages_invalid_role(self):
        """无效角色抛异常"""
        p = self._make_provider()
        messages = [Message(role="invalid", content="hello")]
        with pytest.raises(ValueError, match="无效的消息角色"):
            p.validate_messages(messages)

    def test_validate_messages_empty_content(self):
        """空内容抛异常"""
        p = self._make_provider()
        messages = [Message(role="user", content="   ")]
        with pytest.raises(ValueError, match="消息内容不能为空"):
            p.validate_messages(messages)

    def test_provider_name(self):
        """提供商名称自动推导"""
        p = self._make_provider()
        assert p.name == "concrete"


class TestBaseProviderCostCalculation:
    """测试成本计算"""

    def test_calculate_cost_gpt4o(self):
        """计算GPT-4o成本"""
        usage = Usage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        cost = BaseProvider.calculate_cost(usage, "gpt-4o")
        # input: 1000/1M * 2.50 = 0.0025, output: 500/1M * 10.00 = 0.005, total = 0.0075
        assert cost == pytest.approx(0.0075, rel=0.01)

    def test_calculate_cost_unknown_model(self):
        """未知模型成本为0"""
        usage = Usage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        cost = BaseProvider.calculate_cost(usage, "unknown-model")
        assert cost == 0.0

    def test_calculate_cost_zero_tokens(self):
        """零token成本为0"""
        usage = Usage()
        cost = BaseProvider.calculate_cost(usage, "gpt-4o")
        assert cost == 0.0

    def test_calculate_cost_large_tokens(self):
        """大token量成本计算"""
        usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000)
        cost = BaseProvider.calculate_cost(usage, "gpt-4o")
        # input: 1M/1M * 2.50 = 2.50, output: 1M/1M * 10.00 = 10.00
        assert cost == pytest.approx(12.50, abs=0.01)


# ========== OpenAI Provider测试 ==========


class TestOpenAIProvider:
    """测试OpenAI提供商"""

    def test_init_requires_api_key(self):
        """缺少API密钥抛异常"""
        with pytest.raises(ValueError, match="API密钥未配置"):
            from src.providers.openai import OpenAIProvider
            OpenAIProvider({})

    @patch("src.providers.openai.AsyncOpenAI")
    def test_init_with_api_key(self, mock_openai_class):
        """有API密钥正常初始化"""
        from src.providers.openai import OpenAIProvider
        provider = OpenAIProvider({"api_key": "sk-test", "model": "gpt-4o"})
        assert provider.name == "openai"
        mock_openai_class.assert_called_once_with(api_key="sk-test")

    @patch("src.providers.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_chat(self, mock_openai_class):
        """测试chat方法"""
        from src.providers.openai import OpenAIProvider

        # 设置mock响应
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "你好！"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = OpenAIProvider({"api_key": "sk-test", "model": "gpt-4o"})
        messages = [Message(role="user", content="你好")]
        response = await provider.chat(messages)

        assert response.content == "你好！"
        assert response.model == "gpt-4o"
        assert response.provider == "openai"
        assert response.usage.total_tokens == 15
        assert response.finish_reason == "stop"

    @patch("src.providers.openai.AsyncOpenAI")
    def test_calculate_cost(self, mock_openai_class):
        """OpenAI成本计算"""
        from src.providers.openai import OpenAIProvider
        usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000)
        cost = OpenAIProvider.calculate_cost(usage, "gpt-4o")
        assert cost == pytest.approx(12.50, abs=0.01)

    @patch("src.providers.openai.AsyncOpenAI")
    def test_calculate_cost_mini(self, mock_openai_class):
        """GPT-4o-mini成本计算"""
        from src.providers.openai import OpenAIProvider
        usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000)
        cost = OpenAIProvider.calculate_cost(usage, "gpt-4o-mini")
        assert cost == pytest.approx(0.75, abs=0.01)


# ========== Claude Provider测试 ==========


class TestClaudeProvider:
    """测试Claude提供商"""

    def test_init_requires_api_key(self):
        """缺少API密钥抛异常"""
        with pytest.raises(ValueError, match="API密钥未配置"):
            from src.providers.claude import ClaudeProvider
            ClaudeProvider({})

    @patch("src.providers.claude.anthropic")
    def test_init_with_api_key(self, mock_anthropic):
        """有API密钥正常初始化"""
        from src.providers.claude import ClaudeProvider
        provider = ClaudeProvider({"api_key": "sk-ant-test", "model": "claude-sonnet-4-20250514"})
        assert provider.name == "claude"

    @patch("src.providers.claude.anthropic")
    @pytest.mark.asyncio
    async def test_chat(self, mock_anthropic):
        """测试chat方法"""
        from src.providers.claude import ClaudeProvider

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "你好！"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = ClaudeProvider({"api_key": "sk-ant-test", "model": "claude-sonnet-4-20250514"})
        messages = [Message(role="user", content="你好")]
        response = await provider.chat(messages)

        assert response.content == "你好！"
        assert response.provider == "claude"
        assert response.usage.total_tokens == 15

    @patch("src.providers.claude.anthropic")
    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, mock_anthropic):
        """带系统消息的chat"""
        from src.providers.claude import ClaudeProvider

        mock_client = AsyncMock()
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "好的"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 5
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        provider = ClaudeProvider({"api_key": "sk-ant-test"})
        messages = [
            Message(role="system", content="你是一个助手"),
            Message(role="user", content="你好"),
        ]
        response = await provider.chat(messages)

        assert response.content == "好的"
        # 验证系统消息被正确传递
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs[1]["system"] == "你是一个助手"

    @patch("src.providers.claude.anthropic")
    def test_calculate_cost(self, mock_anthropic):
        """Claude成本计算"""
        from src.providers.claude import ClaudeProvider
        usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000)
        cost = ClaudeProvider.calculate_cost(usage, "claude-sonnet-4-20250514")
        assert cost == pytest.approx(18.00, abs=0.01)


# ========== Ollama Provider测试 ==========


class TestOllamaProvider:
    """测试Ollama提供商"""

    @patch("src.providers.ollama.httpx.AsyncClient")
    def test_init(self, mock_client_class):
        """初始化Ollama"""
        from src.providers.ollama import OllamaProvider
        provider = OllamaProvider({"base_url": "http://localhost:11434", "model": "llama3"})
        assert provider.name == "ollama"
        assert provider.base_url == "http://localhost:11434"

    @patch("src.providers.ollama.httpx.AsyncClient")
    def test_init_default_url(self, mock_client_class):
        """默认URL"""
        from src.providers.ollama import OllamaProvider
        provider = OllamaProvider({})
        assert provider.base_url == "http://localhost:11434"

    @patch("src.providers.ollama.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_chat(self, mock_client_class):
        """测试chat方法"""
        from src.providers.ollama import OllamaProvider

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "你好！"},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "done": True,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        provider = OllamaProvider({"model": "llama3"})
        messages = [Message(role="user", content="你好")]
        response = await provider.chat(messages)

        assert response.content == "你好！"
        assert response.provider == "ollama"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 5
        assert response.finish_reason == "stop"

    @patch("src.providers.ollama.httpx.AsyncClient")
    def test_calculate_cost_zero(self, mock_client_class):
        """Ollama本地模型成本为0"""
        from src.providers.ollama import OllamaProvider
        usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000)
        cost = OllamaProvider.calculate_cost(usage, "llama3")
        assert cost == 0.0

    @patch("src.providers.ollama.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_is_available(self, mock_client_class):
        """检查服务可用性"""
        from src.providers.ollama import OllamaProvider

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = OllamaProvider({})
        result = await provider.is_available()
        assert result is True

    @patch("src.providers.ollama.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_is_not_available(self, mock_client_class):
        """服务不可用"""
        from src.providers.ollama import OllamaProvider

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))

        provider = OllamaProvider({})
        result = await provider.is_available()
        assert result is False

    @patch("src.providers.ollama.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_list_models(self, mock_client_class):
        """列出模型"""
        from src.providers.ollama import OllamaProvider

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:latest"},
                {"name": "mistral:latest"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        provider = OllamaProvider({})
        models = await provider.list_models()
        assert "llama3:latest" in models
        assert "mistral:latest" in models
