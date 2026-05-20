"""成本追踪模块测试"""

import csv
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_assistant.providers.base import Usage


class TestCostTrackerRecord:
    """测试成本记录"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_record_cost(self, mock_config, mock_storage):
        """记录一次调用成本"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()

        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        tracker.record("openai", "gpt-4o", usage, 0.001)

        mock_storage.add_cost_record.assert_called_once_with(
            provider="openai",
            model="gpt-4o",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost=0.001,
        )

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_record_triggers_budget_check(self, mock_config, mock_storage):
        """记录后检查预算"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()

        usage = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        tracker.record("openai", "gpt-4o", usage, 0.001)

        mock_storage.get_recent_cost.assert_called_with(days=30)


class TestCostTrackerBudgetAlert:
    """测试预算警报"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_budget_alert_triggered(self, mock_config, mock_storage, capsys):
        """超预算时发出警报"""
        mock_config.get_budget_alert.return_value = 5.0
        mock_storage.get_recent_cost.return_value = 15.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tracker._check_budget_alert()
        # rich输出到console，我们只验证不抛异常

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_budget_alert_not_triggered(self, mock_config, mock_storage):
        """未超预算时不发警报"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 2.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tracker._check_budget_alert()  # 不应抛异常


class TestCostTrackerStats:
    """测试成本统计"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_get_stats(self, mock_config, mock_storage):
        """获取成本统计"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 0.5,
            "total_tokens": 1000,
            "record_count": 5,
            "by_provider": {"openai": 0.3, "claude": 0.2},
            "by_model": {"gpt-4o": 0.3, "claude-sonnet-4-20250514": 0.2},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        stats = tracker.get_stats()

        assert stats["total_cost"] == 0.5
        assert stats["total_tokens"] == 1000
        assert stats["record_count"] == 5

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_get_stats_with_date_filter(self, mock_config, mock_storage):
        """带日期过滤的统计"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 0.1,
            "total_tokens": 200,
            "record_count": 1,
            "by_provider": {},
            "by_model": {},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        stats = tracker.get_stats(start_date="2024-01-01", end_date="2024-12-31")

        mock_storage.get_cost_stats.assert_called_with(
            start_date="2024-01-01", end_date="2024-12-31"
        )

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_get_monthly_summary(self, mock_config, mock_storage):
        """获取月度摘要"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 1.0,
            "total_tokens": 5000,
            "record_count": 10,
            "by_provider": {},
            "by_model": {},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        summary = tracker.get_monthly_summary()

        assert summary["total_cost"] == 1.0
        # 验证传入了start_date
        call_kwargs = mock_storage.get_cost_stats.call_args
        assert call_kwargs[1]["start_date"] is not None


class TestCostTrackerDisplay:
    """测试成本显示"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_display_stats(self, mock_config, mock_storage):
        """显示成本统计"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()

        stats = {
            "total_cost": 0.5,
            "total_tokens": 1000,
            "record_count": 5,
            "by_provider": {"openai": 0.3, "claude": 0.2},
            "by_model": {"gpt-4o": 0.3},
        }
        tracker.display_stats(stats)  # 不应抛异常

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_display_stats_default(self, mock_config, mock_storage):
        """显示默认统计"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "record_count": 0,
            "by_provider": {},
            "by_model": {},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tracker.display_stats()  # 不应抛异常

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_display_stats_no_providers(self, mock_config, mock_storage):
        """无提供商数据时显示"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()

        stats = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "record_count": 0,
            "by_provider": {},
            "by_model": {},
        }
        tracker.display_stats(stats)


class TestCostTrackerOptimization:
    """测试优化建议"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_optimization_tips_no_data(self, mock_config, mock_storage):
        """无数据时的优化建议"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "record_count": 0,
            "by_provider": {},
            "by_model": {},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tips = tracker.get_optimization_tips()
        assert len(tips) >= 1
        assert "暂无使用记录" in tips[0]

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_optimization_tips_expensive_model(self, mock_config, mock_storage):
        """高花费模型的优化建议"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 5.0,
            "total_tokens": 100000,
            "record_count": 50,
            "by_provider": {"openai": 5.0},
            "by_model": {"gpt-4o": 5.0},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tips = tracker.get_optimization_tips()
        assert any("gpt-4o" in t for t in tips)

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_optimization_tips_no_ollama(self, mock_config, mock_storage):
        """未使用Ollama的优化建议"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 2.0,
            "total_tokens": 50000,
            "record_count": 20,
            "by_provider": {"openai": 2.0},
            "by_model": {"gpt-4o": 2.0},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tips = tracker.get_optimization_tips()
        assert any("ollama" in t.lower() or "本地" in t for t in tips)


class TestCostTrackerBudgetSetting:
    """测试预算设置"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_set_budget_alert(self, mock_config, mock_storage):
        """设置预算警报阈值"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()
        tracker.set_budget_alert(50.0)

        assert tracker.budget_alert == 50.0
        mock_config.set_budget_alert.assert_called_once_with(50.0)


class TestCostTrackerExport:
    """测试CSV导出"""

    @patch("ai_assistant.cost_tracker.storage")
    @patch("ai_assistant.cost_tracker.config")
    def test_export_csv(self, mock_config, mock_storage, tmp_path):
        """导出CSV文件"""
        mock_config.get_budget_alert.return_value = 10.0
        mock_storage.get_recent_cost.return_value = 0.0
        mock_storage.get_cost_stats.return_value = {
            "total_cost": 0.5,
            "total_tokens": 1000,
            "record_count": 5,
            "by_provider": {"openai": 0.3},
            "by_model": {"gpt-4o": 0.3},
        }

        from ai_assistant.cost_tracker import CostTracker
        tracker = CostTracker()

        csv_path = tmp_path / "costs.csv"
        tracker.export_csv(str(csv_path))

        assert csv_path.exists()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) >= 2  # header + data
        assert rows[0] == ["提供商", "模型", "花费"]
