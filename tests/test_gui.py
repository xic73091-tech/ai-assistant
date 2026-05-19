"""GUI基本测试"""

import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_gui_imports():
    """测试GUI模块可以正常导入"""
    from src.gui.chat_widget import ChatWidget, ChatWorker, MessageBubble
    from src.gui.settings_dialog import SettingsDialog
    from src.gui.cost_widget import CostWidget, StatCard
    from src.gui.main_window import MainWindow, NavButton
    from src.gui.app import run_gui
    print("所有GUI模块导入成功")


def test_backend_integration():
    """测试后端模块集成"""
    from src.config import config
    from src.storage import storage
    from src.cost_tracker import cost_tracker
    from src.privacy import privacy_protector
    from src.templates.manager import TemplateManager
    from src.providers.base import Message, ChatResponse, Usage

    # 测试配置
    assert config.get_default_provider() in ("openai", "claude", "ollama")

    # 测试模板
    tm = TemplateManager()
    templates = tm.list_templates()
    assert len(templates) > 0

    # 测试隐私
    assert privacy_protector.get_level_description()

    # 测试成本统计
    stats = cost_tracker.get_stats()
    assert "total_cost" in stats

    print("后端模块集成测试通过")


if __name__ == "__main__":
    test_gui_imports()
    test_backend_integration()
    print("\n所有测试通过!")
