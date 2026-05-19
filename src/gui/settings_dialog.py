"""设置对话框"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import config
from ..privacy import privacy_protector


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(520, 480)
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # 提供商配置标签页
        provider_tab = self._create_provider_tab()
        tabs.addTab(provider_tab, "提供商")

        # 隐私设置标签页
        privacy_tab = self._create_privacy_tab()
        tabs.addTab(privacy_tab, "隐私")

        # 通用设置标签页
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "通用")

        layout.addWidget(tabs)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_provider_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 默认提供商
        default_group = QGroupBox("默认提供商")
        default_layout = QFormLayout(default_group)
        self.default_provider_combo = QComboBox()
        self.default_provider_combo.addItems(["openai", "claude", "ollama"])
        default_layout.addRow("提供商:", self.default_provider_combo)
        layout.addWidget(default_group)

        # OpenAI 配置
        openai_group = QGroupBox("OpenAI")
        openai_layout = QFormLayout(openai_group)
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("sk-...")
        openai_layout.addRow("API Key:", self.openai_key)
        self.openai_model = QLineEdit()
        openai_layout.addRow("模型:", self.openai_model)
        self.openai_max_tokens = QSpinBox()
        self.openai_max_tokens.setRange(1, 128000)
        self.openai_max_tokens.setSingleStep(256)
        openai_layout.addRow("最大Tokens:", self.openai_max_tokens)
        self.openai_temp = QDoubleSpinBox()
        self.openai_temp.setRange(0.0, 2.0)
        self.openai_temp.setSingleStep(0.1)
        self.openai_temp.setDecimals(2)
        openai_layout.addRow("温度:", self.openai_temp)
        layout.addWidget(openai_group)

        # Claude 配置
        claude_group = QGroupBox("Claude")
        claude_layout = QFormLayout(claude_group)
        self.claude_key = QLineEdit()
        self.claude_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.claude_key.setPlaceholderText("sk-ant-...")
        claude_layout.addRow("API Key:", self.claude_key)
        self.claude_model = QLineEdit()
        claude_layout.addRow("模型:", self.claude_model)
        self.claude_max_tokens = QSpinBox()
        self.claude_max_tokens.setRange(1, 200000)
        self.claude_max_tokens.setSingleStep(256)
        claude_layout.addRow("最大Tokens:", self.claude_max_tokens)
        self.claude_temp = QDoubleSpinBox()
        self.claude_temp.setRange(0.0, 1.0)
        self.claude_temp.setSingleStep(0.1)
        self.claude_temp.setDecimals(2)
        claude_layout.addRow("温度:", self.claude_temp)
        layout.addWidget(claude_group)

        # Ollama 配置
        ollama_group = QGroupBox("Ollama (本地)")
        ollama_layout = QFormLayout(ollama_group)
        self.ollama_url = QLineEdit()
        self.ollama_url.setPlaceholderText("http://localhost:11434")
        ollama_layout.addRow("Base URL:", self.ollama_url)
        self.ollama_model = QLineEdit()
        ollama_layout.addRow("模型:", self.ollama_model)
        self.ollama_temp = QDoubleSpinBox()
        self.ollama_temp.setRange(0.0, 2.0)
        self.ollama_temp.setSingleStep(0.1)
        self.ollama_temp.setDecimals(2)
        ollama_layout.addRow("温度:", self.ollama_temp)
        layout.addWidget(ollama_group)

        layout.addStretch()
        return widget

    def _create_privacy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 隐私级别
        level_group = QGroupBox("隐私保护级别")
        level_layout = QFormLayout(level_group)
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItem("低 - 仅检测身份证号、银行卡号和密码", "low")
        self.privacy_combo.addItem("中 - 检测身份证号、手机号、银行卡号和密码", "medium")
        self.privacy_combo.addItem("高 - 检测所有敏感信息", "high")
        level_layout.addRow("级别:", self.privacy_combo)

        self.privacy_desc = QLabel()
        self.privacy_desc.setWordWrap(True)
        self.privacy_desc.setStyleSheet("color: #666; padding: 8px; background: #F9F9F9; border-radius: 4px;")
        level_layout.addRow("", self.privacy_desc)
        self.privacy_combo.currentIndexChanged.connect(self._update_privacy_desc)

        layout.addWidget(level_group)

        # 隐私测试
        test_group = QGroupBox("隐私检测测试")
        test_layout = QVBoxLayout(test_group)
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("输入文本测试隐私检测，如: 我的手机号是13800138000")
        test_layout.addWidget(self.test_input)

        test_btn = QPushButton("测试检测")
        test_btn.clicked.connect(self._run_privacy_test)
        test_layout.addWidget(test_btn)

        self.test_result = QLabel()
        self.test_result.setWordWrap(True)
        self.test_result.setStyleSheet("padding: 8px; background: #F0F0F0; border-radius: 4px;")
        self.test_result.hide()
        test_layout.addWidget(self.test_result)

        layout.addWidget(test_group)
        layout.addStretch()
        return widget

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 存储配置
        storage_group = QGroupBox("存储")
        storage_layout = QFormLayout(storage_group)
        self.storage_path = QLineEdit()
        storage_layout.addRow("数据路径:", self.storage_path)
        self.max_history = QSpinBox()
        self.max_history.setRange(10, 100000)
        storage_layout.addRow("最大历史记录:", self.max_history)
        layout.addWidget(storage_group)

        # 成本配置
        cost_group = QGroupBox("成本管理")
        cost_layout = QFormLayout(cost_group)
        self.budget_alert = QDoubleSpinBox()
        self.budget_alert.setRange(0.0, 100000.0)
        self.budget_alert.setSingleStep(1.0)
        self.budget_alert.setDecimals(2)
        self.budget_alert.setPrefix("$ ")
        cost_layout.addRow("月度预算警报:", self.budget_alert)
        layout.addWidget(cost_group)

        # 重置按钮
        reset_btn = QPushButton("恢复默认配置")
        reset_btn.setStyleSheet("color: #E74C3C;")
        reset_btn.clicked.connect(self._reset_config)
        layout.addWidget(reset_btn)

        layout.addStretch()
        return widget

    def _load_current_settings(self):
        # 提供商
        self.default_provider_combo.setCurrentText(config.get_default_provider())

        # OpenAI
        openai_cfg = config.get_provider_config("openai")
        self.openai_key.setText(openai_cfg.get("api_key", ""))
        self.openai_model.setText(openai_cfg.get("model", "gpt-4o"))
        self.openai_max_tokens.setValue(openai_cfg.get("max_tokens", 4096))
        self.openai_temp.setValue(openai_cfg.get("temperature", 0.7))

        # Claude
        claude_cfg = config.get_provider_config("claude")
        self.claude_key.setText(claude_cfg.get("api_key", ""))
        self.claude_model.setText(claude_cfg.get("model", "claude-sonnet-4-20250514"))
        self.claude_max_tokens.setValue(claude_cfg.get("max_tokens", 4096))
        self.claude_temp.setValue(claude_cfg.get("temperature", 0.7))

        # Ollama
        ollama_cfg = config.get_provider_config("ollama")
        self.ollama_url.setText(ollama_cfg.get("base_url", "http://localhost:11434"))
        self.ollama_model.setText(ollama_cfg.get("model", "llama3"))
        self.ollama_temp.setValue(ollama_cfg.get("temperature", 0.7))

        # 隐私
        level = config.get_privacy_level()
        for i in range(self.privacy_combo.count()):
            if self.privacy_combo.itemData(i) == level:
                self.privacy_combo.setCurrentIndex(i)
                break
        self._update_privacy_desc()

        # 通用
        self.storage_path.setText(str(config.get_storage_path()))
        self.max_history.setValue(config.get("storage.max_history", 1000))
        self.budget_alert.setValue(config.get_budget_alert())

    def _save_settings(self):
        try:
            # 默认提供商
            config.set_default_provider(self.default_provider_combo.currentText())

            # OpenAI
            config.set("providers.openai.api_key", self.openai_key.text())
            config.set("providers.openai.model", self.openai_model.text())
            config.set("providers.openai.max_tokens", self.openai_max_tokens.value())
            config.set("providers.openai.temperature", self.openai_temp.value())

            # Claude
            config.set("providers.claude.api_key", self.claude_key.text())
            config.set("providers.claude.model", self.claude_model.text())
            config.set("providers.claude.max_tokens", self.claude_max_tokens.value())
            config.set("providers.claude.temperature", self.claude_temp.value())

            # Ollama
            config.set("providers.ollama.base_url", self.ollama_url.text())
            config.set("providers.ollama.model", self.ollama_model.text())
            config.set("providers.ollama.temperature", self.ollama_temp.value())

            # 隐私
            privacy_level = self.privacy_combo.currentData()
            config.set_privacy_level(privacy_level)

            # 通用
            config.set("storage.path", self.storage_path.text())
            config.set("storage.max_history", self.max_history.value())
            config.set_budget_alert(self.budget_alert.value())

            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {e}")

    def _update_privacy_desc(self):
        level = self.privacy_combo.currentData()
        descriptions = {
            "low": "低级别保护：仅检测身份证号、银行卡号和密码。适合信任度较高的使用场景。",
            "medium": "中级别保护：检测身份证号、手机号、银行卡号和密码。推荐日常使用。",
            "high": "高级别保护：检测所有敏感信息（身份证、手机、邮箱、银行卡、密码、IP地址）。适合处理高度敏感数据。",
        }
        self.privacy_desc.setText(descriptions.get(level, ""))

    def _run_privacy_test(self):
        text = self.test_input.text()
        if not text:
            return

        level = self.privacy_combo.currentData()
        protector = privacy_protector
        old_level = protector.level
        protector.level = level
        protector.enabled_levels = protector._get_enabled_levels()

        has_sensitive, results = protector.detect(text)
        if has_sensitive:
            masked = protector.mask(text)
            types = ", ".join(set(r.type for r in results))
            self.test_result.setText(
                f"检测到敏感信息 ({types}):\n\n"
                f"原文: {text}\n"
                f"脱敏: {masked}"
            )
            self.test_result.setStyleSheet("padding: 8px; background: #FFF3CD; border-radius: 4px; color: #856404;")
        else:
            self.test_result.setText("未检测到敏感信息")
            self.test_result.setStyleSheet("padding: 8px; background: #D4EDDA; border-radius: 4px; color: #155724;")

        self.test_result.show()
        protector.level = old_level
        protector.enabled_levels = protector._get_enabled_levels()

    def _reset_config(self):
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认配置吗？这将清除所有自定义设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            config.reset()
            self._load_current_settings()
            QMessageBox.information(self, "成功", "已恢复默认配置")
