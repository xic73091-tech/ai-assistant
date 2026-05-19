"""OpenAI提供商"""

from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .base import BaseProvider, ChatResponse, Message, Usage


class OpenAIProvider(BaseProvider):
    """OpenAI API提供商"""

    def __init__(self, config: dict):
        super().__init__(config)
        api_key = config.get("api_key", "")
        if not api_key:
            raise ValueError("OpenAI API密钥未配置")
        self.client = AsyncOpenAI(api_key=api_key)

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

        # 转换消息格式
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = Usage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return ChatResponse(
            content=choice.message.content,
            model=model,
            usage=usage,
            provider=self.name,
            finish_reason=choice.finish_reason,
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

        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        stream = await self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @staticmethod
    def calculate_cost(usage: Usage, model: str) -> float:
        """计算OpenAI调用成本"""
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }
        model_pricing = pricing.get(model, {"input": 0, "output": 0})
        input_cost = (usage.prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)
