"""主窗口"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
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

from .chat_widget import ChatWidget
from .cost_widget import CostWidget
from .settings_dialog import SettingsDialog


class NavButton(QPushButton):
    """导航按钮"""

    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        self.setText(f" {text}")
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setStyleSheet(
            "NavButton {"
            "  text-align: left; padding-left: 16px; border: none; border-radius: 8px;"
            "  font-size: 14px; color: #555; background: transparent;"
            "}"
            "NavButton:hover { background-color: #E8E8E8; }"
            "NavButton:checked {"
            "  background-color: #D6EAF8; color: #2C3E50; font-weight: bold;"
            "}"
        )


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant - 本地化AI助手")
        self.setMinimumSize(1000, 680)
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

        # 左侧导航栏
        nav_panel = QWidget()
        nav_panel.setFixedWidth(180)
        nav_panel.setStyleSheet("background-color: #F7F7F7; border-right: 1px solid #E0E0E0;")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(4)

        # Logo
        logo = QLabel("AI Assistant")
        logo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50; padding: 8px 12px 16px 12px;")
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
        version_label = QLabel("v0.1.0")
        version_label.setStyleSheet("color: #AAA; font-size: 11px; padding: 8px 12px;")
        nav_layout.addWidget(version_label)

        main_layout.addWidget(nav_panel)

        # 右侧内容区域
        self.stack = QStackedWidget()

        self.chat_widget = ChatWidget()
        self.cost_widget = CostWidget()

        self.stack.addWidget(self.chat_widget)   # index 0
        self.stack.addWidget(self.cost_widget)   # index 1

        main_layout.addWidget(self.stack, 1)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.nav_chat.setChecked(index == 0)
        self.nav_cost.setChecked(index == 1)
        self.nav_settings.setChecked(False)

    def _open_settings(self):
        self.nav_chat.setChecked(False)
        self.nav_cost.setChecked(False)
        self.nav_settings.setChecked(True)

        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            # 设置保存后刷新聊天组件的提供商列表
            self.chat_widget._update_model_list()
            self.chat_widget.privacy_label.setText(f"隐私级别: {self.chat_widget.privacy_label.text().split(':')[-1].strip()}")

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
            "<h3>AI Assistant v0.1.0</h3>"
            "<p>本地化AI助手 - 解决回答不准、收费贵、隐私顾虑</p>"
            "<p>支持 OpenAI / Claude / Ollama 多提供商</p>"
            "<p>作者: 守诚知</p>",
        )

    def _apply_global_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QMenuBar {
                background-color: #F7F7F7;
                border-bottom: 1px solid #E0E0E0;
                padding: 2px;
            }
            QMenuBar::item:selected {
                background-color: #D6EAF8;
            }
            QMenu {
                background-color: white;
                border: 1px solid #DDD;
            }
            QMenu::item:selected {
                background-color: #D6EAF8;
            }
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
            QTableWidget::item:selected {
                background-color: #D6EAF8;
            }
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
        """)
