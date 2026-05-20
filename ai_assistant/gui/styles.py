"""GUI样式管理模块

统一管理应用程序的颜色、主题和样式表。
支持深色/浅色主题切换。
"""

from enum import Enum


class Theme(Enum):
    """主题类型"""
    LIGHT = "light"
    DARK = "dark"


# 当前全局主题
_current_theme = Theme.LIGHT


def get_current_theme() -> Theme:
    """获取当前主题"""
    return _current_theme


def set_current_theme(theme: Theme) -> None:
    """设置当前主题"""
    global _current_theme
    _current_theme = theme


def toggle_theme() -> Theme:
    """切换主题，返回切换后的主题"""
    global _current_theme
    _current_theme = Theme.DARK if _current_theme == Theme.LIGHT else Theme.LIGHT
    return _current_theme


# ============ 颜色常量 ============

class Colors:
    """颜色常量"""
    PRIMARY = "#4A90D9"
    PRIMARY_HOVER = "#357ABD"
    PRIMARY_LIGHT = "#D6EAF8"
    SUCCESS = "#2ECC71"
    WARNING = "#F39C12"
    ERROR = "#E74C3C"
    INFO = "#3498DB"


# ============ 样式表生成器 ============

def get_app_stylesheet(theme: Theme = None) -> str:
    """获取应用主样式表"""
    theme = theme or _current_theme
    return _get_dark_stylesheet() if theme == Theme.DARK else _get_light_stylesheet()


def _get_light_stylesheet() -> str:
    return """
        QMainWindow { background-color: #FFFFFF; }
        QMenuBar {
            background-color: #F7F7F7;
            border-bottom: 1px solid #E0E0E0;
            padding: 2px;
        }
        QMenuBar::item:selected { background-color: #D6EAF8; }
        QMenu { background-color: white; border: 1px solid #DDD; }
        QMenu::item:selected { background-color: #D6EAF8; }
        QStatusBar {
            background-color: #F7F7F7;
            border-top: 1px solid #E0E0E0;
            color: #888;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #DDD;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }
        QTableWidget {
            border: 1px solid #DDD;
            border-radius: 4px;
            gridline-color: #EEE;
        }
        QTableWidget::item:selected { background-color: #D6EAF8; }
        QHeaderView::section {
            background-color: #F5F5F5;
            border: none;
            border-bottom: 2px solid #DDD;
            padding: 6px;
            font-weight: bold;
        }
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            padding: 4px 8px;
            border: 1px solid #CCC;
            border-radius: 4px;
            background: white;
        }
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #4A90D9;
        }
        QTabWidget::pane { border: 1px solid #DDD; background: white; }
        QTabBar::tab {
            padding: 8px 16px;
            border: 1px solid #DDD;
            border-bottom: none;
            background: #F5F5F5;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #4A90D9;
        }
    """


def _get_dark_stylesheet() -> str:
    return """
        QMainWindow { background-color: #1E1E1E; }
        QMenuBar {
            background-color: #252526;
            border-bottom: 1px solid #3E3E3E;
            padding: 2px;
            color: #D4D4D4;
        }
        QMenuBar::item:selected { background-color: #094771; }
        QMenu { background-color: #252526; border: 1px solid #3E3E3E; color: #D4D4D4; }
        QMenu::item:selected { background-color: #094771; }
        QStatusBar {
            background-color: #252526;
            border-top: 1px solid #3E3E3E;
            color: #A0A0A0;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #3E3E3E;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 16px;
            color: #D4D4D4;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }
        QTableWidget {
            border: 1px solid #3E3E3E;
            border-radius: 4px;
            gridline-color: #3E3E3E;
            background-color: #1E1E1E;
            color: #D4D4D4;
        }
        QTableWidget::item:selected { background-color: #094771; }
        QHeaderView::section {
            background-color: #252526;
            border: none;
            border-bottom: 2px solid #3E3E3E;
            padding: 6px;
            font-weight: bold;
            color: #D4D4D4;
        }
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            padding: 4px 8px;
            border: 1px solid #3E3E3E;
            border-radius: 4px;
            background: #2D2D2D;
            color: #D4D4D4;
        }
        QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #4A90D9;
        }
        QComboBox QAbstractItemView {
            background-color: #2D2D2D;
            color: #D4D4D4;
            selection-background-color: #094771;
        }
        QTabWidget::pane { border: 1px solid #3E3E3E; background: #1E1E1E; }
        QTabBar::tab {
            padding: 8px 16px;
            border: 1px solid #3E3E3E;
            border-bottom: none;
            background: #252526;
            color: #D4D4D4;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #1E1E1E;
            border-bottom: 2px solid #4A90D9;
        }
    """


def get_nav_stylesheet(theme: Theme = None) -> str:
    """获取导航栏面板样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return "background-color: #252526; border-right: 1px solid #3E3E3E;"
    return "background-color: #F7F7F7; border-right: 1px solid #E0E0E0;"


def get_nav_button_stylesheet(theme: Theme = None) -> str:
    """获取导航按钮样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return (
            "NavButton {"
            "  text-align: left; padding-left: 16px; border: none; border-radius: 8px;"
            "  font-size: 14px; color: #A0A0A0; background: transparent;"
            "}"
            "NavButton:hover { background-color: #2A2D2E; }"
            "NavButton:checked {"
            "  background-color: #094771; color: #D4D4D4; font-weight: bold;"
            "}"
        )
    return (
        "NavButton {"
        "  text-align: left; padding-left: 16px; border: none; border-radius: 8px;"
        "  font-size: 14px; color: #555; background: transparent;"
        "}"
        "NavButton:hover { background-color: #E8E8E8; }"
        "NavButton:checked {"
        "  background-color: #D6EAF8; color: #2C3E50; font-weight: bold;"
        "}"
    )


def get_primary_button_stylesheet() -> str:
    """获取主要操作按钮样式"""
    return (
        "QPushButton { background-color: #4A90D9; color: white; border: none; "
        "border-radius: 4px; padding: 6px 16px; font-weight: bold; }"
        "QPushButton:hover { background-color: #357ABD; }"
        "QPushButton:disabled { background-color: #BDC3C7; }"
    )


def get_send_button_stylesheet() -> str:
    """获取发送按钮样式"""
    return (
        "QPushButton { background-color: #4A90D9; color: white; border: none; "
        "border-radius: 20px; font-weight: bold; }"
        "QPushButton:hover { background-color: #357ABD; }"
        "QPushButton:disabled { background-color: #BDC3C7; }"
    )


def get_message_style(role: str, theme: Theme = None) -> str:
    """获取消息气泡内联样式字符串"""
    theme = theme or _current_theme
    base = "display: inline-block; max-width: 70%; text-align: left;"

    if theme == Theme.DARK:
        styles = {
            "user": (
                f"{base} background-color: #2D4A2D; border-radius: 12px; "
                "padding: 10px 14px; font-size: 14px; color: #D4D4D4;"
            ),
            "assistant": (
                f"{base} background-color: #2D2D2D; border-radius: 12px; "
                "padding: 10px 14px; font-size: 14px; color: #D4D4D4; "
                "border: 1px solid #3E3E3E;"
            ),
            "system": "color: #666; font-size: 12px; font-style: italic;",
        }
    else:
        styles = {
            "user": (
                f"{base} background-color: #DCF8C6; border-radius: 12px; "
                "padding: 10px 14px; font-size: 14px;"
            ),
            "assistant": (
                f"{base} background-color: #FFFFFF; border-radius: 12px; "
                "padding: 10px 14px; font-size: 14px; border: 1px solid #E0E0E0;"
            ),
            "system": "color: #999; font-size: 12px; font-style: italic;",
        }
    return styles.get(role, styles["system"])


def get_avatar_stylesheet(role: str) -> str:
    """获取头像标签样式"""
    if role == "user":
        return (
            "background-color: #4A90D9; color: white; border-radius: 18px; "
            "font-weight: bold; font-size: 11px;"
        )
    return (
        "background-color: #2ECC71; color: white; border-radius: 18px; "
        "font-weight: bold; font-size: 11px;"
    )


def get_toolbar_stylesheet(theme: Theme = None) -> str:
    """获取工具栏样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return "background-color: #252526; border-bottom: 1px solid #3E3E3E; padding: 6px;"
    return "background-color: #F5F5F5; border-bottom: 1px solid #DDD; padding: 6px;"


def get_input_stylesheet(theme: Theme = None) -> str:
    """获取消息输入框样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return (
            "QLineEdit { border: 1px solid #3E3E3E; border-radius: 20px; "
            "padding: 10px 16px; font-size: 14px; background: #2D2D2D; color: #D4D4D4; }"
            "QLineEdit:focus { border-color: #4A90D9; }"
        )
    return (
        "QLineEdit { border: 1px solid #CCC; border-radius: 20px; "
        "padding: 10px 16px; font-size: 14px; background: white; }"
        "QLineEdit:focus { border-color: #4A90D9; }"
    )


def get_chat_background_color(theme: Theme = None) -> str:
    """获取聊天消息区域背景色"""
    theme = theme or _current_theme
    return "#1E1E1E" if theme == Theme.DARK else "#ECE5DD"


def get_status_bar_stylesheet(theme: Theme = None) -> str:
    """获取底部状态栏容器样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return "background-color: #252526; border-top: 1px solid #3E3E3E; padding: 4px 10px;"
    return "background-color: #F0F0F0; border-top: 1px solid #DDD; padding: 4px 10px;"


def get_card_stylesheet(theme: Theme = None) -> str:
    """获取统计卡片容器样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return "background: #2D2D2D; border-radius: 8px; border: 1px solid #3E3E3E;"
    return "background: white; border-radius: 8px; border: 1px solid #E0E0E0;"


def get_label_color(theme: Theme = None, secondary: bool = False) -> str:
    """获取文本标签颜色"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return "#A0A0A0" if secondary else "#D4D4D4"
    return "#888" if secondary else "#333"


def get_history_stylesheet(theme: Theme = None) -> str:
    """获取对话历史列表样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return (
            "QListWidget { border: none; background: transparent; color: #D4D4D4; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #3E3E3E; border-radius: 4px; }"
            "QListWidget::item:selected { background-color: #094771; }"
            "QListWidget::item:hover { background-color: #2A2D2E; }"
        )
    return (
        "QListWidget { border: none; background: transparent; }"
        "QListWidget::item { padding: 8px; border-bottom: 1px solid #EEE; border-radius: 4px; }"
        "QListWidget::item:selected { background-color: #D6EAF8; }"
        "QListWidget::item:hover { background-color: #EBF5FB; }"
    )


def get_history_panel_stylesheet(theme: Theme = None) -> str:
    """获取历史面板容器样式"""
    theme = theme or _current_theme
    if theme == Theme.DARK:
        return "background-color: #1E1E1E; border-right: 1px solid #3E3E3E;"
    return "background-color: #FAFAFA; border-right: 1px solid #DDD;"


def get_chart_colors() -> list[str]:
    """获取图表配色方案"""
    return [
        "#4A90D9", "#E74C3C", "#2ECC71", "#F39C12",
        "#9B59B6", "#1ABC9C", "#E67E22", "#3498DB",
    ]
