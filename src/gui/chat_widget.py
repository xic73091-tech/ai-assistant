"""聊天界面组件"""

import asyncio
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from ..config import config
from ..privacy import privacy_protector
from ..providers.base import ChatResponse, Message, Usage
from ..providers.claude import ClaudeProvider
from ..providers.ollama import OllamaProvider
from ..providers.openai import OpenAIProvider
from ..storage import storage
from ..cost_tracker import cost_tracker
from ..templates.manager import TemplateManager


class ChatWorker(QThread):
    """后台线程执行AI请求"""

    response_ready = pyqtSignal(object)  # ChatResponse
    error_occurred = pyqtSignal(str)
    chunk_received = pyqtSignal(str)

    def __init__(self, provider, messages: list[Message], model: Optional[str], stream: bool = True):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.model = model
        self.stream = stream

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if self.stream:
                response = loop.run_until_complete(self._stream_chat())
            else:
                response = loop.run_until_complete(self._normal_chat())
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            loop.close()

    async def _normal_chat(self) -> ChatResponse:
        return await self.provider.chat(self.messages, model=self.model)

    async def _stream_chat(self) -> ChatResponse:
        full_content = ""
        async for chunk in self.provider.chat_stream(self.messages, model=self.model):
            full_content += chunk
            self.chunk_received.emit(chunk)
        return ChatResponse(
            content=full_content,
            model=self.provider.get_model(self.model),
            usage=Usage(),
            provider=self.provider.name,
        )


class MessageBubble(QWidget):
    """消息气泡"""

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # 头像标签
        avatar = QLabel("You" if role == "user" else "AI")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            "background-color: #4A90D9; color: white; border-radius: 18px; font-weight: bold; font-size: 11px;"
            if role == "user"
            else "background-color: #2ECC71; color: white; border-radius: 18px; font-weight: bold; font-size: 11px;"
        )

        # 消息内容
        bubble = QTextEdit()
        bubble.setReadOnly(True)
        bubble.setPlainText(content)
        bubble.setStyleSheet(
            "background-color: #DCF8C6; border-radius: 8px; padding: 8px; font-size: 14px;"
            if role == "user"
            else "background-color: #FFFFFF; border-radius: 8px; padding: 8px; font-size: 14px; border: 1px solid #E0E0E0;"
        )
        bubble.setMaximumWidth(600)
        bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bubble.document().contentsChanged.connect(self._adjust_height)
        # 触发一次高度调整
        bubble.setMinimumHeight(40)
        bubble.setMaximumHeight(400)

        if role == "user":
            layout.addStretch()
            layout.addWidget(bubble)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addWidget(bubble)
            layout.addStretch()

    def _adjust_height(self):
        doc = self.sender()
        if doc:
            height = int(doc.size().height()) + 16
            self.sender().parent().setMinimumHeight(min(height, 400))


class ChatWidget(QWidget):
    """聊天界面组件"""

    cost_updated = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages: list[Message] = []
        self.conversation_id: Optional[int] = None
        self.template_manager = TemplateManager()
        self.worker: Optional[ChatWorker] = None
        self._setup_ui()
        self._connect_signals()
        self._load_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #F5F5F5; border-bottom: 1px solid #DDD; padding: 6px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 6, 10, 6)

        # 提供商选择
        provider_label = QLabel("提供商:")
        provider_label.setStyleSheet("font-weight: bold; color: #333;")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai", "claude", "ollama"])
        self.provider_combo.setCurrentText(config.get_default_provider())
        self.provider_combo.setStyleSheet("padding: 4px 8px; border: 1px solid #CCC; border-radius: 4px; background: white;")

        # 模型选择
        model_label = QLabel("模型:")
        model_label.setStyleSheet("font-weight: bold; color: #333;")
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self._update_model_list()
        self.model_combo.setStyleSheet("padding: 4px 8px; border: 1px solid #CCC; border-radius: 4px; background: white; min-width: 160px;")

        # 模板选择
        template_label = QLabel("模板:")
        template_label.setStyleSheet("font-weight: bold; color: #333;")
        self.template_combo = QComboBox()
        self.template_combo.addItem("无", None)
        self.template_combo.setStyleSheet("padding: 4px 8px; border: 1px solid #CCC; border-radius: 4px; background: white;")

        # 新建对话按钮
        self.new_chat_btn = QPushButton("新建对话")
        self.new_chat_btn.setStyleSheet(
            "QPushButton { background-color: #4A90D9; color: white; border: none; border-radius: 4px; padding: 6px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #357ABD; }"
        )

        toolbar_layout.addWidget(provider_label)
        toolbar_layout.addWidget(self.provider_combo)
        toolbar_layout.addWidget(model_label)
        toolbar_layout.addWidget(self.model_combo)
        toolbar_layout.addWidget(template_label)
        toolbar_layout.addWidget(self.template_combo)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.new_chat_btn)

        layout.addWidget(toolbar)

        # 对话历史侧边栏 + 聊天区域
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 历史列表
        history_panel = QWidget()
        history_panel.setStyleSheet("background-color: #FAFAFA; border-right: 1px solid #DDD;")
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(8, 8, 8, 8)

        history_label = QLabel("对话历史")
        history_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; padding: 4px 0;")
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(
            "QListWidget { border: none; background: transparent; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #EEE; border-radius: 4px; }"
            "QListWidget::item:selected { background-color: #D6EAF8; }"
            "QListWidget::item:hover { background-color: #EBF5FB; }"
        )
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_list)

        splitter.addWidget(history_panel)

        # 聊天主区域
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # 消息显示区域
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setStyleSheet(
            "background-color: #ECE5DD; border: none; padding: 10px; font-size: 14px;"
        )

        # 输入区域
        input_area = QWidget()
        input_area.setStyleSheet("background-color: #F5F5F5; border-top: 1px solid #DDD; padding: 8px;")
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(10, 8, 10, 8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息... (Enter 发送)")
        self.input_field.setStyleSheet(
            "QLineEdit { border: 1px solid #CCC; border-radius: 20px; padding: 10px 16px; font-size: 14px; background: white; }"
            "QLineEdit:focus { border-color: #4A90D9; }"
        )

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(60, 40)
        self.send_btn.setStyleSheet(
            "QPushButton { background-color: #4A90D9; color: white; border: none; border-radius: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #357ABD; }"
            "QPushButton:disabled { background-color: #BDC3C7; }"
        )

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(self.message_display, 1)
        chat_layout.addWidget(input_area, 0)

        splitter.addWidget(chat_panel)
        splitter.setSizes([200, 600])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # 底部状态栏
        status_bar = QWidget()
        status_bar.setStyleSheet("background-color: #F0F0F0; border-top: 1px solid #DDD; padding: 4px 10px;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 4, 10, 4)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        self.cost_label = QLabel("费用: $0.0000")
        self.cost_label.setStyleSheet("color: #888; font-size: 12px;")
        self.token_label = QLabel("Tokens: 0")
        self.token_label.setStyleSheet("color: #888; font-size: 12px;")
        self.privacy_label = QLabel(f"隐私级别: {config.get_privacy_level()}")
        self.privacy_label.setStyleSheet("color: #888; font-size: 12px;")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.privacy_label)
        status_layout.addWidget(self.token_label)
        status_layout.addWidget(self.cost_label)

        layout.addWidget(status_bar)

    def _connect_signals(self):
        self.send_btn.clicked.connect(self._send_message)
        self.input_field.returnPressed.connect(self._send_message)
        self.new_chat_btn.clicked.connect(self._new_conversation)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.history_list.currentItemChanged.connect(self._on_history_selected)

    def _load_templates(self):
        for t in self.template_manager.list_templates():
            self.template_combo.addItem(f"{t['name']} - {t['description']}", t['name'])

    def _update_model_list(self):
        provider = self.provider_combo.currentText()
        self.model_combo.clear()
        models = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "claude": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001", "claude-opus-4-7"],
            "ollama": ["llama3", "mistral", "codellama"],
        }
        self.model_combo.addItems(models.get(provider, []))
        # 从配置获取默认模型
        provider_config = config.get_provider_config(provider)
        default_model = provider_config.get("model", "")
        idx = self.model_combo.findText(default_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def _on_provider_changed(self, provider: str):
        self._update_model_list()

    def _get_provider(self):
        name = self.provider_combo.currentText()
        provider_config = config.get_provider_config(name)
        if name == "openai":
            return OpenAIProvider(provider_config)
        elif name == "claude":
            return ClaudeProvider(provider_config)
        elif name == "ollama":
            return OllamaProvider(provider_config)
        raise ValueError(f"不支持的提供商: {name}")

    def _new_conversation(self):
        self.messages.clear()
        self.message_display.clear()
        self.conversation_id = None
        self.status_label.setText("新对话")
        self._refresh_history()

    def _send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        # 隐私检查
        has_sensitive, results = privacy_protector.detect(text)
        if has_sensitive:
            masked = privacy_protector.mask(text)
            reply = QMessageBox.question(
                self, "隐私提示",
                f"检测到敏感信息，是否自动脱敏后发送？\n\n原文: {text[:100]}...\n脱敏: {masked[:100]}...",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                text = masked

        self.input_field.clear()
        self._append_message("user", text)

        # 创建对话记录
        if self.conversation_id is None:
            provider_name = self.provider_combo.currentText()
            model_name = self.model_combo.currentText()
            self.conversation_id = storage.create_conversation(
                title=text[:30] + ("..." if len(text) > 30 else ""),
                provider=provider_name,
                model=model_name,
            )

        # 构建消息列表
        self.messages.append(Message(role="user", content=text))
        storage.add_message(self.conversation_id, "user", text)

        # 处理模板
        template_name = self.template_combo.currentData()
        messages_to_send = list(self.messages)
        if template_name:
            template_obj = self.template_manager.get_template(template_name)
            if template_obj:
                # 如果是第一条消息，加入系统提示词
                if len(messages_to_send) == 1:
                    messages_to_send.insert(0, Message(role="system", content=template_obj.get_system_prompt()))

        # 禁用输入
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        self.status_label.setText("正在生成回复...")

        # 启动后台线程
        try:
            provider = self._get_provider()
        except ValueError as e:
            self._append_message("system", f"错误: {e}")
            self.send_btn.setEnabled(True)
            self.input_field.setEnabled(True)
            return

        model = self.model_combo.currentText() or None
        self.worker = ChatWorker(provider, messages_to_send, model, stream=False)
        self.worker.response_ready.connect(self._on_response)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.chunk_received.connect(self._on_chunk)
        self.worker.start()

    def _on_response(self, response: ChatResponse):
        self._append_message("assistant", response.content)
        self.messages.append(Message(role="assistant", content=response.content))

        # 计算并记录成本
        provider_name = self.provider_combo.currentText()
        provider_cls = {"openai": OpenAIProvider, "claude": ClaudeProvider, "ollama": OllamaProvider}
        cls = provider_cls.get(provider_name)
        cost = cls.calculate_cost(response.usage, response.model) if cls else 0.0
        cost_tracker.record(
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            cost=cost,
        )
        storage.add_message(
            self.conversation_id, "assistant", response.content,
            tokens=response.usage.total_tokens, cost=cost,
        )

        self.cost_label.setText(f"费用: ${cost:.4f}")
        self.token_label.setText(f"Tokens: {response.usage.total_tokens:,}")
        self.status_label.setText("就绪")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.cost_updated.emit(cost)
        self._refresh_history()

    def _on_error(self, error_msg: str):
        self._append_message("system", f"请求失败: {error_msg}")
        self.status_label.setText("错误")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)

    def _on_chunk(self, chunk: str):
        # 流式模式下追加内容到当前显示
        pass

    def _append_message(self, role: str, content: str):
        html = self._format_message_html(role, content)
        self.message_display.moveCursor(QTextCursor.MoveOperation.End)
        self.message_display.insertHtml(html)
        self.message_display.moveCursor(QTextCursor.MoveOperation.End)

    def _format_message_html(self, role: str, content: str) -> str:
        # 转义HTML
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = content.replace("\n", "<br>")

        if role == "user":
            return (
                f'<div style="margin: 8px 0; text-align: right;">'
                f'<span style="background-color: #DCF8C6; padding: 8px 12px; border-radius: 12px; '
                f'display: inline-block; max-width: 70%; text-align: left; font-size: 14px;">'
                f'{content}</span></div>'
            )
        elif role == "assistant":
            return (
                f'<div style="margin: 8px 0; text-align: left;">'
                f'<span style="background-color: #FFFFFF; padding: 8px 12px; border-radius: 12px; '
                f'display: inline-block; max-width: 70%; text-align: left; font-size: 14px; '
                f'border: 1px solid #E0E0E0;">'
                f'{content}</span></div>'
            )
        else:  # system
            return (
                f'<div style="margin: 4px 0; text-align: center;">'
                f'<span style="color: #999; font-size: 12px; font-style: italic;">'
                f'{content}</span></div>'
            )

    def _refresh_history(self):
        self.history_list.clear()
        conversations = storage.list_conversations(30)
        for conv in conversations:
            item = QListWidgetItem(f"{conv['title']}\n{conv['provider']} | {conv['updated_at'][:16]}")
            item.setData(Qt.ItemDataRole.UserRole, conv['id'])
            self.history_list.addItem(item)

    def _on_history_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current is None:
            return
        conv_id = current.data(Qt.ItemDataRole.UserRole)
        self._load_conversation(conv_id)

    def _load_conversation(self, conversation_id: int):
        conv = storage.get_conversation(conversation_id)
        if not conv:
            return
        self.conversation_id = conversation_id
        self.messages.clear()
        self.message_display.clear()

        # 设置提供商和模型
        idx = self.provider_combo.findText(conv['provider'])
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        idx = self.model_combo.findText(conv['model'])
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

        # 加载消息
        msgs = storage.get_conversation_messages(conversation_id)
        for msg in msgs:
            self._append_message(msg['role'], msg['content'])
            self.messages.append(Message(role=msg['role'], content=msg['content']))

        self.status_label.setText(f"已加载对话: {conv['title'][:30]}")
