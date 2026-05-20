"""主窗口"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
)

from .. import __version__
from ..config import config
from .chat_widget import ChatWidget
from .cost_widget import CostWidget
from .settings_dialog import SettingsDialog
from .styles import (
    Theme,
    get_current_theme,
    set_current_theme,
    toggle_theme,
    get_app_stylesheet,
    get_nav_stylesheet,
    get_nav_button_stylesheet,
    get_label_color,
)


class NavButton(QPushButton):
    """导航按钮"""

    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        self.setText(f" {text}")
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setStyleSheet(get_nav_button_stylesheet())


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant - 本地化AI助手")
        # 基于屏幕分辨率设置最小尺寸，适配不同显示器
        screen = QApplication.primaryScreen().geometry()
        width = max(800, min(1000, int(screen.width() * 0.6)))
        height = max(500, min(680, int(screen.height() * 0.7)))
        self.setMinimumSize(width, height)
        self._setup_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._apply_global_style()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏（宽度在resizeEvent中动态调整）
        self.nav_panel = QWidget()
        self.nav_panel.setMinimumWidth(150)
        self.nav_panel.setMaximumWidth(250)
        self.nav_panel.setStyleSheet(get_nav_stylesheet())
        nav_layout = QVBoxLayout(self.nav_panel)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(4)

        # Logo
        logo = QLabel("AI Assistant")
        logo.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {get_label_color()}; "
            "padding: 8px 12px 16px 12px;"
        )
        nav_layout.addWidget(logo)

        # 导航按钮
        self.nav_chat = NavButton("对话")
        self.nav_cost = NavButton("成本统计")
        self.nav_settings = NavButton("设置")

        self.nav_chat.setChecked(True)

        self.nav_chat.clicked.connect(lambda: self._switch_page(0))
        self.nav_cost.clicked.connect(lambda: self._switch_page(1))
        self.nav_settings.clicked.connect(self._open_settings)

        nav_layout.addWidget(self.nav_chat)
        nav_layout.addWidget(self.nav_cost)
        nav_layout.addWidget(self.nav_settings)
        nav_layout.addStretch()

        # 版本信息
        version_label = QLabel(f"v{__version__}")
        version_label.setStyleSheet(
            f"color: {get_label_color(secondary=True)}; font-size: 11px; padding: 8px 12px;"
        )
        nav_layout.addWidget(version_label)

        main_layout.addWidget(self.nav_panel)

        # 右侧内容区域
        self.stack = QStackedWidget()

        self.chat_widget = ChatWidget()
        self.cost_widget = CostWidget()

        self.stack.addWidget(self.chat_widget)  # index 0
        self.stack.addWidget(self.cost_widget)  # index 1

        main_layout.addWidget(self.stack, 1)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.nav_chat.setChecked(index == 0)
        self.nav_cost.setChecked(index == 1)
        self.nav_settings.setChecked(False)

    def resizeEvent(self, event):
        """窗口大小改变时动态调整导航栏宽度"""
        super().resizeEvent(event)
        nav_width = max(150, min(250, int(event.size().width() * 0.15)))
        self.nav_panel.setFixedWidth(nav_width)

    def _open_settings(self):
        self.nav_chat.setChecked(False)
        self.nav_cost.setChecked(False)
        self.nav_settings.setChecked(True)

        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self.chat_widget._update_model_list()
            self.chat_widget.privacy_label.setText(
                f"隐私级别: {config.get_privacy_level()}"
            )

        self.nav_settings.setChecked(False)
        self._switch_page(self.stack.currentIndex())

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")

        new_action = QAction("新建对话(&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.chat_widget._new_conversation)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        settings_action = QAction("设置(&S)...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 视图菜单
        view_menu = menu_bar.addMenu("视图(&V)")

        chat_action = QAction("对话(&C)", self)
        chat_action.setShortcut("Ctrl+1")
        chat_action.triggered.connect(lambda: self._switch_page(0))
        view_menu.addAction(chat_action)

        cost_action = QAction("成本统计(&S)", self)
        cost_action.setShortcut("Ctrl+2")
        cost_action.triggered.connect(lambda: self._switch_page(1))
        view_menu.addAction(cost_action)

        view_menu.addSeparator()

        # 主题切换
        theme_menu = view_menu.addMenu("主题(&T)")
        self.light_action = QAction("浅色主题", self)
        self.light_action.setCheckable(True)
        self.light_action.setChecked(get_current_theme() == Theme.LIGHT)
        self.light_action.triggered.connect(lambda: self._switch_theme(Theme.LIGHT))
        theme_menu.addAction(self.light_action)

        self.dark_action = QAction("深色主题", self)
        self.dark_action.setCheckable(True)
        self.dark_action.setChecked(get_current_theme() == Theme.DARK)
        self.dark_action.triggered.connect(lambda: self._switch_theme(Theme.DARK))
        theme_menu.addAction(self.dark_action)

        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { border-bottom: 1px solid #E0E0E0; spacing: 4px; }")
        self.addToolBar(toolbar)

        new_chat_action = QAction("新建对话", self)
        new_chat_action.triggered.connect(self.chat_widget._new_conversation)
        toolbar.addAction(new_chat_action)

        toolbar.addSeparator()

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._open_settings)
        toolbar.addAction(settings_action)

    def _create_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("就绪")

    def _show_about(self):
        QMessageBox.about(
            self,
            "关于 AI Assistant",
            "<h3>AI Assistant v0.2.0</h3>"
            "<p>本地化AI助手 - 解决回答不准、收费贵、隐私顾虑</p>"
            "<p>支持 OpenAI / Claude / Ollama / MiMo 多提供商</p>"
            "<p>作者: 守诚知</p>",
        )

    def _apply_global_style(self):
        self.setStyleSheet(get_app_stylesheet())

    def _switch_theme(self, theme: Theme):
        """切换主题"""
        set_current_theme(theme)
        self.light_action.setChecked(theme == Theme.LIGHT)
        self.dark_action.setChecked(theme == Theme.DARK)

        # 更新全局样式
        self._apply_global_style()

        # 更新导航栏
        self.nav_panel.setStyleSheet(get_nav_stylesheet())
        for btn in [self.nav_chat, self.nav_cost, self.nav_settings]:
            btn.setStyleSheet(get_nav_button_stylesheet())

        # 更新子组件
        self.chat_widget.apply_theme()
        self.cost_widget.apply_theme()
