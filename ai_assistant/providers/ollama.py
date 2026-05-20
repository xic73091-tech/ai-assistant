"""Ollama本地模型提供商"""

from typing import AsyncIterator, Optional

import httpx

from .base import BaseProvider, ChatResponse, Message, Usage


class OllamaProvider(BaseProvider):
    """Ollama本地模型提供商"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

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

        # 转换消息格式
        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self.client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": ollama_messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        response.raise_for_status()
        data = response.json()

        usage = Usage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        )

        return ChatResponse(
            content=data["message"]["content"],
            model=model,
            usage=usage,
            provider=self.name,
            finish_reason="stop" if data.get("done") else None,
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

        ollama_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        async with self.client.stream(
            "POST",
            "/api/chat",
            json={
                "model": model,
                "messages": ollama_messages,
                "stream": True,
                "options": {"temperature": temperature},
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data:
                        yield data["message"]["content"]

    @staticmethod
    def calculate_cost(usage: Usage, model: str) -> float:
        """Ollama本地模型无成本"""
        return 0.0

    async def list_models(self) -> list[str]:
        """列出可用模型"""
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]

    async def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False
