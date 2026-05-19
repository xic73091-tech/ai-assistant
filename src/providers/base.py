"""AI提供商基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional


@dataclass
class Message:
    """消息数据类"""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class Usage:
    """使用量统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str
    usage: Usage
    provider: str
    finish_reason: Optional[str] = None


class BaseProvider(ABC):
    """AI提供商基类"""

    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """发送聊天请求"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """流式聊天请求"""
        pass

    def get_model(self, model: Optional[str] = None) -> str:
        """获取模型名称"""
        return model or self.config.get("model", "")

    def get_temperature(self, temperature: Optional[float] = None) -> float:
        """获取温度参数"""
        return temperature if temperature is not None else self.config.get("temperature", 0.7)

    def get_max_tokens(self, max_tokens: Optional[int] = None) -> int:
        """获取最大token数"""
        return max_tokens or self.config.get("max_tokens", 4096)

    def validate_messages(self, messages: list[Message]) -> None:
        """验证消息格式"""
        if not messages:
            raise ValueError("消息列表不能为空")
        for msg in messages:
            if msg.role not in ("user", "assistant", "system"):
                raise ValueError(f"无效的消息角色: {msg.role}")
            if not msg.content.strip():
                raise ValueError("消息内容不能为空")

    @staticmethod
    def calculate_cost(usage: Usage, model: str) -> float:
        """计算调用成本（美元）"""
        # 默认价格表，子类可以覆盖
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
        }
        # 每百万token的价格
        model_pricing = pricing.get(model, {"input": 0, "output": 0})
        input_cost = (usage.prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)
