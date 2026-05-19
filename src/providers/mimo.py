"""MiMo提供商（兼容OpenAI接口协议）"""

from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .base import BaseProvider, ChatResponse, Message, Usage


class MiMoProvider(BaseProvider):
    """MiMo API提供商（兼容OpenAI接口协议）"""

    def __init__(self, config: dict):
        super().__init__(config)
        api_key = config.get("api_key", "")
        if not api_key:
            raise ValueError("MiMo API密钥未配置")
        base_url = config.get("base_url", "https://token-plan-cn.xiaomimimo.com/v1")
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

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
        mimo_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self.client.chat.completions.create(
            model=model,
            messages=mimo_messages,
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

        mimo_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        stream = await self.client.chat.completions.create(
            model=model,
            messages=mimo_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @staticmethod
    def calculate_cost(usage: Usage, model: str) -> float:
        """计算MiMo调用成本（基于Credits）"""
        # MiMo使用Credits系统，这里简化计算
        # 实际价格需要根据官方文档调整
        pricing = {
            "MiMo-V2.5-Pro": {"input": 0.002, "output": 0.006},
            "MiMo-V2.5": {"input": 0.001, "output": 0.003},
            "MiMo-V2-Pro": {"input": 0.0015, "output": 0.004},
        }
        model_pricing = pricing.get(model, {"input": 0.001, "output": 0.003})
        input_cost = (usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)

    def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        return [
            "mimo-v2.5-pro",
            "mimo-v2.5",
            "mimo-v2-pro",
            "mimo-v2-omni",
        ]
