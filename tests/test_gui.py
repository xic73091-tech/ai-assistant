"""GUI测试"""

import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_gui_imports():
    """测试GUI模块可以正常导入"""
    from src.gui.styles import (
        Theme, get_app_stylesheet, get_message_style, get_nav_button_stylesheet,
        get_current_theme, set_current_theme, toggle_theme,
        get_toolbar_stylesheet, get_input_stylesheet, get_chat_background_color,
        get_status_bar_stylesheet, get_card_stylesheet, get_label_color,
        get_history_stylesheet, get_primary_button_stylesheet,
        get_send_button_stylesheet, get_avatar_stylesheet, get_chart_colors,
    )
    from src.gui.chat_widget import (
        ChatWidget, ChatWorker, MessageBubble, MarkdownRenderer, SyntaxHighlighter,
    )
    from src.gui.settings_dialog import SettingsDialog
    from src.gui.cost_widget import CostWidget, StatCard, BarChartWidget
    from src.gui.main_window import MainWindow, NavButton
    from src.gui.app import run_gui
    print("所有GUI模块导入成功")


def test_markdown_renderer():
    """测试Markdown渲染器"""
    from src.gui.chat_widget import MarkdownRenderer

    # 测试标题
    html = MarkdownRenderer.to_html("# Hello")
    assert "Hello" in html
    assert "font-weight: bold" in html

    # 测试多级标题
    html = MarkdownRenderer.to_html("## H2\n### H3")
    assert "H2" in html
    assert "H3" in html

    # 测试加粗
    html = MarkdownRenderer.to_html("**bold text**")
    assert "<b>bold text</b>" in html

    # 测试斜体
    html = MarkdownRenderer.to_html("*italic text*")
    assert "<i>italic text</i>" in html

    # 测试行内代码
    html = MarkdownRenderer.to_html("`code`")
    assert "<code" in html
    assert "code</code>" in html

    # 测试代码块
    html = MarkdownRenderer.to_html("```python\nprint('hello')\n```")
    assert "<pre" in html
    assert "print" in html

    # 测试无语言代码块
    html = MarkdownRenderer.to_html("```\nsome code\n```")
    assert "<pre" in html
    assert "some code" in html

    # 测试无序列表
    html = MarkdownRenderer.to_html("- item1\n- item2")
    assert "<ul" in html
    assert "<li>" in html
    assert "item1" in html
    assert "item2" in html

    # 测试有序列表
    html = MarkdownRenderer.to_html("1. first\n2. second")
    assert "<ol" in html
    assert "<li>" in html
    assert "first" in html

    # 测试链接
    html = MarkdownRenderer.to_html("[link](http://example.com)")
    assert "href" in html
    assert "link" in html

    # 测试引用块
    html = MarkdownRenderer.to_html("> quoted text")
    assert "blockquote" in html
    assert "quoted text" in html

    # 测试分割线
    html = MarkdownRenderer.to_html("---")
    assert "<hr" in html

    # 测试删除线
    html = MarkdownRenderer.to_html("~~deleted~~")
    assert "<s>deleted</s>" in html

    # 测试混合内容
    html = MarkdownRenderer.to_html(
        "Hello **world**\n\n```python\ndef foo():\n    pass\n```\n\n- item1"
    )
    assert "<b>world</b>" in html
    assert "<pre" in html
    assert "def" in html
    assert "<ul" in html

    # 测试HTML转义（安全）
    html = MarkdownRenderer.to_html("Hello <script>alert('xss')</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

    print("Markdown渲染器测试通过")


def test_syntax_highlighter():
    """测试语法高亮器"""
    from src.gui.chat_widget import SyntaxHighlighter

    # 测试Python高亮
    code = "def hello():\n    print('hello')"
    html = SyntaxHighlighter.highlight(code, "python")
    assert "def" in html
    assert "print" in html
    assert "color:" in html  # 应有高亮颜色

    # 测试JavaScript高亮
    code = "function hello() {\n    console.log('hello');\n}"
    html = SyntaxHighlighter.highlight(code, "javascript")
    assert "function" in html

    # 测试SQL高亮
    code = "SELECT * FROM users WHERE id = 1"
    html = SyntaxHighlighter.highlight(code, "sql")
    assert "SELECT" in html
    assert "FROM" in html

    # 测试通用高亮
    code = "some code\n123"
    html = SyntaxHighlighter.highlight(code, "")
    assert "123" in html

    # 测试注释高亮
    code = "# this is a comment\ncode = 1"
    html = SyntaxHighlighter.highlight(code, "python")
    assert "comment" in html
    assert "font-style: italic" in html

    # 测试多行代码
    code = "line1\nline2\nline3"
    html = SyntaxHighlighter.highlight(code, "")
    assert "<br>" in html  # 行间用<br>分隔

    print("语法高亮器测试通过")


def test_styles():
    """测试样式模块"""
    from src.gui.styles import (
        Theme, get_app_stylesheet, get_message_style, get_nav_button_stylesheet,
        get_current_theme, set_current_theme, toggle_theme,
        get_toolbar_stylesheet, get_input_stylesheet, get_chat_background_color,
        get_status_bar_stylesheet, get_card_stylesheet, get_label_color,
        get_primary_button_stylesheet, get_send_button_stylesheet,
        get_avatar_stylesheet, get_chart_colors, get_history_stylesheet,
    )

    # 测试浅色主题
    light_css = get_app_stylesheet(Theme.LIGHT)
    assert "#FFFFFF" in light_css or "#F7F7F7" in light_css

    # 测试深色主题
    dark_css = get_app_stylesheet(Theme.DARK)
    assert "#1E1E1E" in dark_css or "#252526" in dark_css

    # 测试消息样式
    user_style = get_message_style("user", Theme.LIGHT)
    assert "DCF8C6" in user_style

    assistant_style = get_message_style("assistant", Theme.LIGHT)
    assert "FFFFFF" in assistant_style

    system_style = get_message_style("system", Theme.LIGHT)
    assert "italic" in system_style

    # 测试深色消息样式
    dark_user = get_message_style("user", Theme.DARK)
    assert "2D4A2D" in dark_user

    # 测试导航按钮样式
    nav_style = get_nav_button_stylesheet(Theme.LIGHT)
    assert "NavButton" in nav_style

    dark_nav = get_nav_button_stylesheet(Theme.DARK)
    assert "NavButton" in dark_nav

    # 测试主题切换
    original = get_current_theme()
    set_current_theme(Theme.DARK)
    assert get_current_theme() == Theme.DARK
    set_current_theme(Theme.LIGHT)
    assert get_current_theme() == Theme.LIGHT

    result = toggle_theme()
    assert result == Theme.DARK
    assert get_current_theme() == Theme.DARK
    toggle_theme()  # 切回

    # 测试工具栏样式
    assert "padding" in get_toolbar_stylesheet()
    assert "padding" in get_toolbar_stylesheet(Theme.DARK)

    # 测试输入框样式
    assert "border-radius" in get_input_stylesheet()
    assert "border-radius" in get_input_stylesheet(Theme.DARK)

    # 测试背景色
    assert get_chat_background_color(Theme.LIGHT) == "#ECE5DD"
    assert get_chat_background_color(Theme.DARK) == "#1E1E1E"

    # 测试状态栏样式
    assert "padding" in get_status_bar_stylesheet()
    assert "padding" in get_status_bar_stylesheet(Theme.DARK)

    # 测试卡片样式
    assert "border-radius" in get_card_stylesheet()
    assert "border-radius" in get_card_stylesheet(Theme.DARK)

    # 测试标签颜色
    assert get_label_color(Theme.LIGHT) == "#333"
    assert get_label_color(Theme.LIGHT, secondary=True) == "#888"
    assert get_label_color(Theme.DARK) == "#D4D4D4"
    assert get_label_color(Theme.DARK, secondary=True) == "#A0A0A0"

    # 测试按钮样式
    assert "4A90D9" in get_primary_button_stylesheet()
    assert "4A90D9" in get_send_button_stylesheet()

    # 测试头像样式
    assert "4A90D9" in get_avatar_stylesheet("user")
    assert "2ECC71" in get_avatar_stylesheet("assistant")

    # 测试历史列表样式
    assert "QListWidget" in get_history_stylesheet()
    assert "QListWidget" in get_history_stylesheet(Theme.DARK)

    # 测试图表颜色
    colors = get_chart_colors()
    assert len(colors) > 0
    assert all(c.startswith("#") for c in colors)

    print("样式模块测试通过")


def test_backend_integration():
    """测试后端模块集成"""
    from src.config import config
    from src.storage import storage
    from src.cost_tracker import cost_tracker
    from src.privacy import privacy_protector
    from src.templates.manager import TemplateManager
    from src.providers.base import Message, ChatResponse, Usage

    # 测试配置
    assert config.get_default_provider() in ("openai", "claude", "ollama", "mimo")

    # 测试MiMo配置存在
    mimo_cfg = config.get_provider_config("mimo")
    assert "api_key" in mimo_cfg
    assert "base_url" in mimo_cfg
    assert "model" in mimo_cfg

    # 测试模板
    tm = TemplateManager()
    templates = tm.list_templates()
    assert len(templates) > 0

    # 测试隐私
    assert privacy_protector.get_level_description()

    # 测试隐私检测（修复后的接口）
    results = privacy_protector.detect("我的手机号是13800138000")
    assert isinstance(results, list)
    # check_and_warn返回元组
    has_sensitive, warn_results = privacy_protector.check_and_warn("我的手机号是13800138000")
    assert isinstance(has_sensitive, bool)
    assert isinstance(warn_results, list)

    # 测试成本统计
    stats = cost_tracker.get_stats()
    assert "total_cost" in stats
    assert "total_tokens" in stats
    assert "record_count" in stats
    assert "by_provider" in stats
    assert "by_model" in stats

    print("后端模块集成测试通过")


def test_provider_integration():
    """测试提供商集成（GUI层面）"""
    from src.gui.chat_widget import ChatWidget

    # 测试提供商模型映射
    assert "openai" in ChatWidget.PROVIDER_MODELS
    assert "claude" in ChatWidget.PROVIDER_MODELS
    assert "ollama" in ChatWidget.PROVIDER_MODELS
    assert "mimo" in ChatWidget.PROVIDER_MODELS

    # 测试提供商类映射
    assert "openai" in ChatWidget.PROVIDER_CLASSES
    assert "claude" in ChatWidget.PROVIDER_CLASSES
    assert "ollama" in ChatWidget.PROVIDER_CLASSES
    assert "mimo" in ChatWidget.PROVIDER_CLASSES

    # 测试MiMo模型列表
    mimo_models = ChatWidget.PROVIDER_MODELS["mimo"]
    assert "mimo-v2.5-pro" in mimo_models

    print("提供商集成测试通过")


if __name__ == "__main__":
    test_gui_imports()
    test_markdown_renderer()
    test_syntax_highlighter()
    test_styles()
    test_backend_integration()
    test_provider_integration()
    print("\n所有测试通过!")
