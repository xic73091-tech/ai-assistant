"""Claude提供商"""

from typing import AsyncIterator, Optional

import anthropic

from .base import BaseProvider, ChatResponse, Message, Usage


class ClaudeProvider(BaseProvider):
    """Claude API提供商"""

    def __init__(self, config: dict):
        super().__init__(config)
        api_key = config.get("api_key", "")
        if not api_key:
            raise ValueError("Claude API密钥未配置")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """发送聊天请求"""
        self.validate_messages(messages)

        model = self.get_model(model)
        temperature = self.get_temperature(temperature)
        max_tokens = self.get_max_tokens(max_tokens)

        # 分离系统消息
        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_message:
            kwargs["system"] = system_message

        response = await self.client.messages.create(**kwargs)

        usage = Usage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )

        return ChatResponse(
            content=response.content[0].text,
            model=model,
            usage=usage,
            provider=self.name,
            finish_reason=response.stop_reason,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """流式聊天请求"""
        self.validate_messages(messages)

        model = self.get_model(model)
        temperature = self.get_temperature(temperature)
        max_tokens = self.get_max_tokens(max_tokens)

        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_message:
            kwargs["system"] = system_message

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    @staticmethod
    def calculate_cost(usage: Usage, model: str) -> float:
        """计算Claude调用成本"""
        pricing = {
            "claude-opus-4-7": {"input": 15.00, "output": 75.00},
            "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
            "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
        }
        model_pricing = pricing.get(model, {"input": 0, "output": 0})
        input_cost = (usage.prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)
