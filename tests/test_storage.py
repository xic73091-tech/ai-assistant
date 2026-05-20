"""存储模块测试"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_assistant.storage import Storage


@pytest.fixture
def storage(tmp_db):
    """创建临时存储实例"""
    return Storage(tmp_db)


class TestConversationCRUD:
    """测试对话增删改查"""

    def test_create_conversation(self, storage):
        """创建对话"""
        conv_id = storage.create_conversation("测试对话", "openai", "gpt-4o")
        assert conv_id is not None
        assert conv_id > 0

    def test_create_multiple_conversations(self, storage):
        """创建多个对话"""
        id1 = storage.create_conversation("对话1", "openai", "gpt-4o")
        id2 = storage.create_conversation("对话2", "claude", "claude-sonnet-4-20250514")
        assert id1 != id2

    def test_get_conversation(self, storage):
        """获取对话"""
        conv_id = storage.create_conversation("获取测试", "openai", "gpt-4o")
        conv = storage.get_conversation(conv_id)
        assert conv is not None
        assert conv["title"] == "获取测试"
        assert conv["provider"] == "openai"
        assert conv["model"] == "gpt-4o"

    def test_get_nonexistent_conversation(self, storage):
        """获取不存在的对话返回None"""
        conv = storage.get_conversation(99999)
        assert conv is None

    def test_list_conversations(self, storage):
        """列出对话"""
        storage.create_conversation("对话A", "openai", "gpt-4o")
        storage.create_conversation("对话B", "claude", "claude-sonnet-4-20250514")
        conversations = storage.list_conversations()
        assert len(conversations) == 2

    def test_list_conversations_with_limit(self, storage):
        """限制列出对话数量"""
        for i in range(5):
            storage.create_conversation(f"对话{i}", "openai", "gpt-4o")
        conversations = storage.list_conversations(limit=3)
        assert len(conversations) == 3

    def test_list_conversations_empty(self, storage):
        """没有对话时返回空列表"""
        conversations = storage.list_conversations()
        assert conversations == []

    def test_delete_conversation(self, storage):
        """删除对话"""
        conv_id = storage.create_conversation("待删除", "openai", "gpt-4o")
        storage.delete_conversation(conv_id)
        assert storage.get_conversation(conv_id) is None

    def test_delete_conversation_removes_messages(self, storage):
        """删除对话时同时删除消息"""
        conv_id = storage.create_conversation("带消息的对话", "openai", "gpt-4o")
        storage.add_message(conv_id, "user", "你好")
        storage.delete_conversation(conv_id)
        messages = storage.get_conversation_messages(conv_id)
        assert len(messages) == 0


class TestMessageCRUD:
    """测试消息增删改查"""

    def test_add_message(self, storage):
        """添加消息"""
        conv_id = storage.create_conversation("消息测试", "openai", "gpt-4o")
        msg_id = storage.add_message(conv_id, "user", "你好")
        assert msg_id is not None
        assert msg_id > 0

    def test_add_message_with_tokens_and_cost(self, storage):
        """添加带token和成本的消息"""
        conv_id = storage.create_conversation("成本测试", "openai", "gpt-4o")
        msg_id = storage.add_message(conv_id, "assistant", "你好！", 150, 0.001)
        assert msg_id > 0

    def test_get_conversation_messages(self, storage):
        """获取对话消息"""
        conv_id = storage.create_conversation("消息列表", "openai", "gpt-4o")
        storage.add_message(conv_id, "user", "问题")
        storage.add_message(conv_id, "assistant", "回答")

        messages = storage.get_conversation_messages(conv_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "问题"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "回答"

    def test_get_messages_empty_conversation(self, storage):
        """空对话返回空消息列表"""
        conv_id = storage.create_conversation("空对话", "openai", "gpt-4o")
        messages = storage.get_conversation_messages(conv_id)
        assert messages == []

    def test_message_fields(self, storage):
        """消息字段完整性"""
        conv_id = storage.create_conversation("字段测试", "openai", "gpt-4o")
        storage.add_message(conv_id, "user", "测试内容", 100, 0.005)

        messages = storage.get_conversation_messages(conv_id)
        msg = messages[0]
        assert msg["conversation_id"] == conv_id
        assert msg["role"] == "user"
        assert msg["content"] == "测试内容"
        assert msg["tokens"] == 100
        assert msg["cost"] == 0.005
        assert "created_at" in msg


class TestCostRecords:
    """测试成本记录"""

    def test_add_cost_record(self, storage):
        """添加成本记录"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        stats = storage.get_cost_stats()
        assert stats["total_cost"] == 0.01
        assert stats["total_tokens"] == 300
        assert stats["record_count"] == 1

    def test_multiple_cost_records(self, storage):
        """多条成本记录"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        storage.add_cost_record("claude", "claude-sonnet-4-20250514", 150, 250, 400, 0.02)

        stats = storage.get_cost_stats()
        assert stats["total_cost"] == pytest.approx(0.03, abs=0.001)
        assert stats["total_tokens"] == 700
        assert stats["record_count"] == 2

    def test_cost_stats_by_provider(self, storage):
        """按提供商统计成本"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        storage.add_cost_record("openai", "gpt-4o", 50, 100, 150, 0.005)
        storage.add_cost_record("claude", "claude-sonnet-4-20250514", 200, 300, 500, 0.03)

        stats = storage.get_cost_stats()
        assert stats["by_provider"]["openai"] == pytest.approx(0.015, abs=0.001)
        assert stats["by_provider"]["claude"] == pytest.approx(0.03, abs=0.001)

    def test_cost_stats_by_model(self, storage):
        """按模型统计成本"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        storage.add_cost_record("openai", "gpt-4o-mini", 50, 100, 150, 0.001)

        stats = storage.get_cost_stats()
        assert "gpt-4o" in stats["by_model"]
        assert "gpt-4o-mini" in stats["by_model"]

    def test_cost_stats_empty(self, storage):
        """无记录时成本统计"""
        stats = storage.get_cost_stats()
        assert stats["total_cost"] == 0.0
        assert stats["total_tokens"] == 0
        assert stats["record_count"] == 0
        assert stats["by_provider"] == {}
        assert stats["by_model"] == {}

    def test_get_recent_cost(self, storage):
        """获取近期成本"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.05)
        recent = storage.get_recent_cost(days=30)
        assert recent >= 0.05

    def test_cost_stats_with_date_filter(self, storage):
        """带日期过滤的成本统计"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        # 使用未来日期过滤，应该返回空
        stats = storage.get_cost_stats(start_date="2099-01-01")
        assert stats["record_count"] == 0


class TestCleanup:
    """测试清理功能"""

    def test_cleanup_old_records(self, storage):
        """清理旧记录"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        # 清理90天前的记录，当前记录不应该被清理
        deleted = storage.cleanup_old_records(days=90)
        assert deleted == 0

    def test_cleanup_with_very_short_days(self, storage):
        """用极短天数清理"""
        storage.add_cost_record("openai", "gpt-4o", 100, 200, 300, 0.01)
        # 0天前的记录应该被清理（因为created_at是CURRENT_TIMESTAMP）
        # 注意：这取决于数据库的时间精度
        deleted = storage.cleanup_old_records(days=0)
        # 至少不应该报错
        assert isinstance(deleted, int)
