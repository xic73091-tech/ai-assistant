"""聊天界面组件"""

import asyncio
import re
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
from ..providers.mimo import MiMoProvider
from ..providers.ollama import OllamaProvider
from ..providers.openai import OpenAIProvider
from ..storage import storage
from ..cost_tracker import cost_tracker
from ..templates.manager import TemplateManager
from .styles import (
    get_current_theme,
    get_toolbar_stylesheet,
    get_primary_button_stylesheet,
    get_send_button_stylesheet,
    get_message_style,
    get_avatar_stylesheet,
    get_input_stylesheet,
    get_chat_background_color,
    get_status_bar_stylesheet,
    get_label_color,
    get_history_panel_stylesheet,
    get_history_stylesheet,
)


# ============ Markdown渲染器 ============

class MarkdownRenderer:
    """将Markdown文本转换为HTML，用于QTextEdit显示"""

    @staticmethod
    def to_html(text: str) -> str:
        """将Markdown文本转换为HTML"""
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 提取代码块，用占位符保护
        code_blocks: list[tuple[str, str]] = []

        def _save_code_block(match: re.Match) -> str:
            lang = match.group(1) or ''
            code = match.group(2)
            idx = len(code_blocks)
            code_blocks.append((lang, code))
            return f'\x00CB{idx}\x00'

        text = re.sub(r'```(\w*)\n(.*?)\n?```', _save_code_block, text, flags=re.DOTALL)

        # 逐行处理
        lines = text.split('\n')
        html_parts: list[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 代码块占位符
            cb_match = re.match(r'^\x00CB(\d+)\x00$', stripped)
            if cb_match:
                idx = int(cb_match.group(1))
                lang, code = code_blocks[idx]
                highlighted = SyntaxHighlighter.highlight(code, lang)
                html_parts.append(
                    '<pre style="background: #282C34; color: #ABB2BF; padding: 12px; '
                    'border-radius: 6px; font-family: Consolas, \'Courier New\', monospace; '
                    'font-size: 13px; display: block; white-space: pre-wrap; '
                    'word-wrap: break-word;"><code>'
                    f'{highlighted}</code></pre>'
                )
                i += 1
                continue

            # 标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                content = MarkdownRenderer._process_inline(header_match.group(2))
                size = max(14, 24 - (level - 1) * 2)
                html_parts.append(
                    f'<p style="font-size: {size}px; font-weight: bold; '
                    f'margin: 8px 0 4px 0;">{content}</p>'
                )
                i += 1
                continue

            # 水平分割线
            if re.match(r'^[-*_]{3,}\s*$', stripped):
                html_parts.append(
                    '<hr style="border: none; border-top: 1px solid #DDD; margin: 8px 0;">'
                )
                i += 1
                continue

            # 引用块
            if stripped.startswith('>'):
                content = MarkdownRenderer._process_inline(stripped[1:].strip())
                html_parts.append(
                    '<blockquote style="border-left: 3px solid #4A90D9; '
                    'padding-left: 12px; color: #666; margin: 4px 0;">'
                    f'{content}</blockquote>'
                )
                i += 1
                continue

            # 无序列表
            ul_match = re.match(r'^[\s]*[-*+]\s+(.+)$', line)
            if ul_match:
                items: list[str] = []
                while i < len(lines):
                    m = re.match(r'^[\s]*[-*+]\s+(.+)$', lines[i])
                    if m:
                        items.append(MarkdownRenderer._process_inline(m.group(1)))
                        i += 1
                    else:
                        break
                html_parts.append(
                    '<ul style="margin: 4px 0; padding-left: 20px;">'
                    + ''.join(f'<li>{item}</li>' for item in items)
                    + '</ul>'
                )
                continue

            # 有序列表
            ol_match = re.match(r'^[\s]*\d+\.\s+(.+)$', line)
            if ol_match:
                items = []
                while i < len(lines):
                    m = re.match(r'^[\s]*\d+\.\s+(.+)$', lines[i])
                    if m:
                        items.append(MarkdownRenderer._process_inline(m.group(1)))
                        i += 1
                    else:
                        break
                html_parts.append(
                    '<ol style="margin: 4px 0; padding-left: 20px;">'
                    + ''.join(f'<li>{item}</li>' for item in items)
                    + '</ol>'
                )
                continue

            # 空行
            if not stripped:
                html_parts.append('<br>')
                i += 1
                continue

            # 普通文本段落
            content = MarkdownRenderer._process_inline(line)
            html_parts.append(f'<p style="margin: 2px 0;">{content}</p>')
            i += 1

        return '\n'.join(html_parts)

    @staticmethod
    def _process_inline(text: str) -> str:
        """处理行内Markdown元素"""
        # 先转义HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # 行内代码（先处理以保护内容）
        text = re.sub(
            r'`([^`]+)`',
            (
                '<code style="background: #F0F0F0; padding: 2px 6px; border-radius: 3px; '
                'font-family: Consolas, monospace; font-size: 13px;">\\1</code>'
            ),
            text,
        )

        # 加粗
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

        # 斜体
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<i>\1</i>', text)

        # 删除线
        text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)

        # 链接
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2" style="color: #4A90D9;">\1</a>',
            text,
        )

        return text


# ============ 语法高亮器 ============

class SyntaxHighlighter:
    """简单的代码语法高亮器"""

    PYTHON_KEYWORDS = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
        'try', 'while', 'with', 'yield',
    }

    PYTHON_BUILTINS = {
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
        'set', 'tuple', 'type', 'isinstance', 'hasattr', 'getattr', 'super',
        'property', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
        'any', 'all', 'min', 'max', 'sum', 'abs', 'round', 'open', 'input',
        'format', 'repr', 'bool', 'bytes', 'object', 'vars', 'dir', 'callable',
    }

    JS_KEYWORDS = {
        'async', 'await', 'break', 'case', 'catch', 'class', 'const',
        'continue', 'debugger', 'default', 'delete', 'do', 'else', 'export',
        'extends', 'false', 'finally', 'for', 'function', 'if', 'import',
        'in', 'instanceof', 'let', 'new', 'null', 'return', 'super', 'switch',
        'this', 'throw', 'true', 'try', 'typeof', 'undefined', 'var', 'void',
        'while', 'with', 'yield',
    }

    SQL_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL',
        'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE',
        'TABLE', 'DROP', 'ALTER', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
        'ON', 'AS', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'UNION',
        'ALL', 'DISTINCT', 'INDEX', 'VIEW',
    }

    SQL_BUILTINS = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'IF', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'}

    @classmethod
    def highlight(cls, code: str, language: str = '') -> str:
        """高亮代码并返回HTML（用<br>换行）"""
        lang = language.lower().strip()
        lines = code.split('\n')
        result = [cls._highlight_line(line, lang) for line in lines]
        return '<br>'.join(result)

    @classmethod
    def _highlight_line(cls, line: str, language: str) -> str:
        """高亮单行代码"""
        # 转义HTML
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # 根据语言确定参数
        if language in ('python', 'py'):
            comment_char = '#'
            keywords = cls.PYTHON_KEYWORDS
            builtins = cls.PYTHON_BUILTINS
        elif language in ('javascript', 'js', 'typescript', 'ts', 'jsx', 'tsx'):
            comment_char = '//'
            keywords = cls.JS_KEYWORDS
            builtins = set()
        elif language in ('sql',):
            comment_char = '--'
            keywords = cls.SQL_KEYWORDS
            builtins = cls.SQL_BUILTINS
        elif language in ('bash', 'sh', 'shell', 'zsh', 'ruby', 'rb'):
            comment_char = '#'
            keywords = set()
            builtins = set()
        else:
            comment_char = '#'
            keywords = set()
            builtins = set()

        # 整行注释
        stripped = line.lstrip()
        if comment_char and stripped.startswith(comment_char):
            return f'<span style="color: #5C6370; font-style: italic;">{line}</span>'

        # 高亮关键字
        if keywords:
            kw_pattern = '|'.join(re.escape(kw) for kw in keywords)
            line = re.sub(
                rf'\b({kw_pattern})\b',
                r'<span style="color: #C678DD;">\1</span>',
                line,
            )

        # 高亮内置函数/类型
        if builtins:
            bi_pattern = '|'.join(re.escape(bi) for bi in builtins)
            line = re.sub(
                rf'\b({bi_pattern})\b',
                r'<span style="color: #61AFEF;">\1</span>',
                line,
            )

        # 高亮数字
        line = re.sub(
            r'\b(\d+\.?\d*(?:[eE][+-]?\d+)?)\b',
            r'<span style="color: #D19A66;">\1</span>',
            line,
        )

        # 高亮字符串（HTML转义后的引号）
        line = re.sub(
            r'(&quot;)(?:(?!\1).)*?\1',
            lambda m: f'<span style="color: #98C379;">{m.group()}</span>',
            line,
        )
        line = re.sub(
            r'(&#39;)(?:(?!\1).)*?\1',
            lambda m: f'<span style="color: #98C379;">{m.group()}</span>',
            line,
        )

        return line


# ============ 后台工作线程 ============

class ChatWorker(QThread):
    """后台线程执行AI请求"""

    response_ready = pyqtSignal(object)  # ChatResponse
    error_occurred = pyqtSignal(str)
    chunk_received = pyqtSignal(str)

    def __init__(
        self,
        provider,
        messages: list[Message],
        model: Optional[str],
        stream: bool = True,
    ):
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


# ============ 消息气泡组件 ============

class MessageBubble(QWidget):
    """消息气泡（独立组件，可用于自定义布局）"""

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        avatar = QLabel("You" if role == "user" else "AI")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(get_avatar_stylesheet(role))

        bubble = QTextEdit()
        bubble.setReadOnly(True)
        if role == "assistant":
            bubble.setHtml(MarkdownRenderer.to_html(content))
        else:
            bubble.setPlainText(content)
        bubble.setStyleSheet(get_message_style(role))
        bubble.setMaximumWidth(600)
        bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bubble.document().contentsChanged.connect(self._adjust_height)
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
            parent_widget = self.sender().parent()
            if parent_widget:
                parent_widget.setMinimumHeight(min(height, 400))


# ============ 聊天主界面 ============

class ChatWidget(QWidget):
    """聊天界面组件"""

    cost_updated = pyqtSignal(float)

    # 提供商 -> 模型列表映射
    PROVIDER_MODELS = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "claude": [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-7",
        ],
        "ollama": ["llama3", "mistral", "codellama"],
        "mimo": ["mimo-v2.5-pro", "mimo-v2.5", "mimo-v2-pro", "mimo-v2-omni"],
    }

    # 提供商 -> 类映射（用于成本计算）
    PROVIDER_CLASSES = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
        "mimo": MiMoProvider,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages: list[Message] = []
        self.conversation_id: Optional[int] = None
        self.template_manager = TemplateManager()
        self.worker: Optional[ChatWorker] = None
        self._stream_buffer = ""
        self._stream_response_start = 0
        self._setup_ui()
        self._connect_signals()
        self._load_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- 顶部工具栏 ----
        toolbar = QWidget()
        toolbar.setStyleSheet(get_toolbar_stylesheet())
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 6, 10, 6)

        provider_label = QLabel("提供商:")
        provider_label.setStyleSheet(f"font-weight: bold; color: {get_label_color()};")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(self.PROVIDER_MODELS.keys()))
        self.provider_combo.setCurrentText(config.get_default_provider())
        self.provider_combo.setStyleSheet(
            "padding: 4px 8px; border: 1px solid #CCC; border-radius: 4px; background: white;"
        )

        model_label = QLabel("模型:")
        model_label.setStyleSheet(f"font-weight: bold; color: {get_label_color()};")
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self._update_model_list()
        self.model_combo.setStyleSheet(
            "padding: 4px 8px; border: 1px solid #CCC; border-radius: 4px; "
            "background: white; min-width: 160px;"
        )

        template_label = QLabel("模板:")
        template_label.setStyleSheet(f"font-weight: bold; color: {get_label_color()};")
        self.template_combo = QComboBox()
        self.template_combo.addItem("无", None)
        self.template_combo.setStyleSheet(
            "padding: 4px 8px; border: 1px solid #CCC; border-radius: 4px; background: white;"
        )

        self.new_chat_btn = QPushButton("新建对话")
        self.new_chat_btn.setStyleSheet(get_primary_button_stylesheet())

        toolbar_layout.addWidget(provider_label)
        toolbar_layout.addWidget(self.provider_combo)
        toolbar_layout.addWidget(model_label)
        toolbar_layout.addWidget(self.model_combo)
        toolbar_layout.addWidget(template_label)
        toolbar_layout.addWidget(self.template_combo)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.new_chat_btn)

        layout.addWidget(toolbar)

        # ---- 对话历史 + 聊天区域 ----
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 历史列表
        history_panel = QWidget()
        history_panel.setStyleSheet(get_history_panel_stylesheet())
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(8, 8, 8, 8)

        history_label = QLabel("对话历史")
        history_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {get_label_color()}; padding: 4px 0;"
        )
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(get_history_stylesheet())
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_list)

        splitter.addWidget(history_panel)

        # 聊天主区域
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setStyleSheet(
            f"background-color: {get_chat_background_color()}; "
            "border: none; padding: 10px; font-size: 14px;"
        )

        # 输入区域
        input_area = QWidget()
        input_area.setStyleSheet(
            "background-color: #F5F5F5; border-top: 1px solid #DDD; padding: 8px;"
        )
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(10, 8, 10, 8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息... (Enter 发送)")
        self.input_field.setStyleSheet(get_input_stylesheet())

        self.send_btn = QPushButton("发送")
        self.send_btn.setMinimumSize(60, 40)
        self.send_btn.setStyleSheet(get_send_button_stylesheet())

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(self.message_display, 1)
        chat_layout.addWidget(input_area, 0)

        splitter.addWidget(chat_panel)
        # 使用比例而非固定像素，初始25%/75%
        total_width = max(800, self.width() if self.width() > 0 else 1000)
        splitter.setSizes([int(total_width * 0.25), int(total_width * 0.75)])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # ---- 底部状态栏 ----
        status_bar = QWidget()
        status_bar.setStyleSheet(get_status_bar_stylesheet())
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 4, 10, 4)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {get_label_color(secondary=True)}; font-size: 12px;")
        self.cost_label = QLabel("费用: $0.0000")
        self.cost_label.setStyleSheet(f"color: {get_label_color(secondary=True)}; font-size: 12px;")
        self.token_label = QLabel("Tokens: 0")
        self.token_label.setStyleSheet(f"color: {get_label_color(secondary=True)}; font-size: 12px;")
        self.privacy_label = QLabel(f"隐私级别: {config.get_privacy_level()}")
        self.privacy_label.setStyleSheet(f"color: {get_label_color(secondary=True)}; font-size: 12px;")

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
            self.template_combo.addItem(
                f"{t['name']} - {t['description']}", t['name']
            )

    def _update_model_list(self):
        provider = self.provider_combo.currentText()
        self.model_combo.clear()
        self.model_combo.addItems(self.PROVIDER_MODELS.get(provider, []))
        provider_cfg = config.get_provider_config(provider)
        default_model = provider_cfg.get("model", "")
        idx = self.model_combo.findText(default_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

    def _on_provider_changed(self, provider: str):
        self._update_model_list()

    def _get_provider(self):
        name = self.provider_combo.currentText()
        provider_config = config.get_provider_config(name)
        cls = self.PROVIDER_CLASSES.get(name)
        if cls is None:
            raise ValueError(f"不支持的提供商: {name}")
        return cls(provider_config)

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

        # 如果上一个请求还在进行中，忽略
        if self.worker and self.worker.isRunning():
            return

        # 隐私检查（修复：detect()返回列表，不是元组）
        results = privacy_protector.detect(text)
        has_sensitive = len(results) > 0
        if has_sensitive:
            masked = privacy_protector.mask(text)
            types = ", ".join(set(r.type for r in results))
            reply = QMessageBox.question(
                self,
                "隐私提示",
                f"检测到敏感信息 ({types})，是否自动脱敏后发送？\n\n"
                f"原文: {text[:100]}...\n脱敏: {masked[:100]}...",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
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
            if template_obj and len(messages_to_send) == 1:
                messages_to_send.insert(
                    0, Message(role="system", content=template_obj.get_system_prompt())
                )

        # 禁用输入
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        self.status_label.setText("正在生成回复...")

        # 准备流式输出
        self._stream_buffer = ""
        cursor = self.message_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._stream_response_start = cursor.position()

        # 启动后台线程
        try:
            provider = self._get_provider()
        except ValueError as e:
            self._append_message("system", f"错误: {e}")
            self.send_btn.setEnabled(True)
            self.input_field.setEnabled(True)
            return

        model = self.model_combo.currentText() or None
        self.worker = ChatWorker(provider, messages_to_send, model, stream=True)
        self.worker.response_ready.connect(self._on_response)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.chunk_received.connect(self._on_chunk)
        self.worker.start()

    def _on_chunk(self, chunk: str):
        """流式输出：接收chunk并更新显示"""
        self._stream_buffer += chunk
        # 替换从流式起点到末尾的内容
        cursor = self.message_display.textCursor()
        cursor.setPosition(self._stream_response_start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()
        # 用简单的HTML显示流式内容（不做Markdown渲染以提高性能）
        escaped = (
            self._stream_buffer
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('\n', '<br>')
        )
        style = get_message_style("assistant")
        cursor.insertHtml(
            f'<div style="margin: 8px 0; text-align: left;">'
            f'<span style="{style}">{escaped}</span></div>'
        )
        self.message_display.setTextCursor(cursor)
        self.message_display.ensureCursorVisible()

    def _on_response(self, response: ChatResponse):
        """请求完成：用Markdown渲染替换流式内容"""
        # 替换流式内容为完整Markdown渲染
        cursor = self.message_display.textCursor()
        cursor.setPosition(self._stream_response_start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()

        # 插入Markdown渲染后的消息
        html = self._format_message_html("assistant", response.content)
        cursor.insertHtml(html)
        cursor.insertHtml('<br>')
        self.message_display.setTextCursor(cursor)
        self.message_display.ensureCursorVisible()

        # 存储消息
        self.messages.append(Message(role="assistant", content=response.content))

        # 计算并记录成本
        provider_name = self.provider_combo.currentText()
        cls = self.PROVIDER_CLASSES.get(provider_name)
        cost = cls.calculate_cost(response.usage, response.model) if cls else 0.0
        cost_tracker.record(
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            cost=cost,
        )
        storage.add_message(
            self.conversation_id,
            "assistant",
            response.content,
            tokens=response.usage.total_tokens,
            cost=cost,
        )

        self.cost_label.setText(f"费用: ${cost:.4f}")
        self.token_label.setText(f"Tokens: {response.usage.total_tokens:,}")
        self.status_label.setText("就绪")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.cost_updated.emit(cost)
        self._refresh_history()

    def _on_error(self, error_msg: str):
        """请求出错：清理流式内容并显示错误"""
        # 移除未完成的流式内容
        cursor = self.message_display.textCursor()
        cursor.setPosition(self._stream_response_start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()

        self._append_message("system", f"请求失败: {error_msg}")
        self.status_label.setText("错误")
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)

    def _append_message(self, role: str, content: str):
        """向消息显示区追加一条消息"""
        html = self._format_message_html(role, content)
        cursor = self.message_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        cursor.insertHtml('<br>')
        self.message_display.setTextCursor(cursor)
        self.message_display.ensureCursorVisible()

    def _format_message_html(self, role: str, content: str) -> str:
        """将消息格式化为HTML"""
        style = get_message_style(role)

        if role == "user":
            escaped = (
                content.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('\n', '<br>')
            )
            return (
                f'<div style="margin: 8px 0; text-align: right;">'
                f'<span style="{style}">{escaped}</span></div>'
            )
        elif role == "assistant":
            rendered = MarkdownRenderer.to_html(content)
            return (
                f'<div style="margin: 8px 0; text-align: left;">'
                f'<span style="{style}">{rendered}</span></div>'
            )
        else:  # system
            escaped = (
                content.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
            )
            return (
                f'<div style="margin: 4px 0; text-align: center;">'
                f'<span style="{style}">{escaped}</span></div>'
            )

    def _refresh_history(self):
        self.history_list.clear()
        conversations = storage.list_conversations(30)
        for conv in conversations:
            item = QListWidgetItem(
                f"{conv['title']}\n{conv['provider']} | {conv['updated_at'][:16]}"
            )
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

        idx = self.provider_combo.findText(conv['provider'])
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        idx = self.model_combo.findText(conv['model'])
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

        msgs = storage.get_conversation_messages(conversation_id)
        for msg in msgs:
            self._append_message(msg['role'], msg['content'])
            self.messages.append(Message(role=msg['role'], content=msg['content']))

        self.status_label.setText(f"已加载对话: {conv['title'][:30]}")

    def apply_theme(self) -> None:
        """应用当前主题样式（供外部调用）"""
        from .styles import get_current_theme
        theme = get_current_theme()
        self.message_display.setStyleSheet(
            f"background-color: {get_chat_background_color(theme)}; "
            "border: none; padding: 10px; font-size: 14px;"
        )
