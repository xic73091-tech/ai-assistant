"""多语言支持模块"""

from typing import Any

from .config import config


# 翻译字典
TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh": {
        # 通用
        "app_name": "AI Assistant",
        "welcome": "欢迎",
        "goodbye": "再见！",
        "error": "错误",
        "success": "成功",
        "cancel": "取消",
        "confirm": "确认",
        "yes": "是",
        "no": "否",

        # 对话
        "chat_start": "输入消息开始对话，输入 'quit' 退出，输入 'help' 查看帮助",
        "chat_provider": "提供商",
        "chat_model": "模型",
        "chat_privacy_level": "隐私级别",
        "chat_interrupted": "对话已中断",
        "chat_template_hint": "模板变量请在消息中使用 {变量名} 格式",
        "chat_using_template": "使用模板",

        # 帮助
        "help_title": "命令帮助",
        "help_quit": "退出对话",
        "help_cost": "查看成本统计",
        "help_tips": "查看成本优化建议",
        "help_help": "显示此帮助信息",
        "help_search": "联网搜索 (如: /search 天气)",
        "help_file": "加载文件到上下文 (如: /file path/to/file)",
        "help_export": "导出对话 (如: /export md)",

        # 成本
        "cost_title": "成本统计总览",
        "cost_total": "总花费",
        "cost_tokens": "总Token数",
        "cost_records": "记录数",
        "cost_by_provider": "按提供商统计",
        "cost_by_model": "按模型统计",
        "cost_optimization": "成本优化建议",
        "cost_exported": "成本记录已导出到 {path}",
        "cost_budget_warning": "警告：本月已花费 ${cost}，超过预算阈值 ${threshold}",

        # 搜索
        "search_title": "联网搜索",
        "search_query": "搜索查询",
        "searching": "正在搜索: {query}",
        "search_results": "搜索结果",
        "search_no_results": "未找到相关结果",
        "search_error": "搜索失败: {error}",
        "search_source": "来源",
        "search_provider": "搜索引擎",

        # 文件处理
        "file_loading": "正在加载文件: {path}",
        "file_loaded": "文件已加载 ({size} 字符)",
        "file_error": "文件处理失败: {error}",
        "file_not_found": "文件不存在: {path}",
        "file_unsupported": "不支持的文件格式: {format}",
        "file_too_large": "文件过大 ({size} 字符)，超过限制 ({limit} 字符)",
        "file_content_header": "以下是文件 {name} 的内容：\n\n",

        # 导出
        "export_title": "导出对话",
        "export_success": "对话已导出到 {path}",
        "export_error": "导出失败: {error}",
        "export_format": "导出格式",
        "export_no_conversation": "没有可导出的对话",
        "export_cost_report": "成本报告",

        # 配置
        "config_title": "当前配置",
        "config_set_success": "{key} 已设置为 {value}",
        "config_set_fail": "设置失败: {error}",

        # 隐私
        "privacy_detected": "检测到敏感信息：",
        "privacy_masked": "已自动脱敏处理",
        "privacy_level_set": "隐私保护级别已设置为 {level}",
        "privacy_no_sensitive": "未检测到敏感信息",

        # 模板
        "template_title": "提示词模板",
        "template_not_found": "模板 '{name}' 不存在",
        "template_available": "可用模板：",

        # 历史
        "history_title": "对话历史",
        "history_empty": "暂无对话记录",

        # 语言
        "lang_set": "语言已设置为 {lang}",
        "lang_current": "当前语言: {lang}",
        "lang_supported": "支持的语言: zh (中文), en (English)",
    },
    "en": {
        # General
        "app_name": "AI Assistant",
        "welcome": "Welcome",
        "goodbye": "Goodbye!",
        "error": "Error",
        "success": "Success",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "yes": "Yes",
        "no": "No",

        # Chat
        "chat_start": "Type a message to start chatting, 'quit' to exit, 'help' for help",
        "chat_provider": "Provider",
        "chat_model": "Model",
        "chat_privacy_level": "Privacy Level",
        "chat_interrupted": "Chat interrupted",
        "chat_template_hint": "Use {variable} format for template variables in messages",
        "chat_using_template": "Using template",

        # Help
        "help_title": "Command Help",
        "help_quit": "Exit chat",
        "help_cost": "View cost statistics",
        "help_tips": "View cost optimization tips",
        "help_help": "Show this help",
        "help_search": "Web search (e.g.: /search weather)",
        "help_file": "Load file to context (e.g.: /file path/to/file)",
        "help_export": "Export chat (e.g.: /export md)",

        # Cost
        "cost_title": "Cost Statistics Overview",
        "cost_total": "Total Cost",
        "cost_tokens": "Total Tokens",
        "cost_records": "Records",
        "cost_by_provider": "By Provider",
        "cost_by_model": "By Model",
        "cost_optimization": "Cost Optimization Tips",
        "cost_exported": "Cost records exported to {path}",
        "cost_budget_warning": "Warning: Spent ${cost} this month, exceeding budget threshold ${threshold}",

        # Search
        "search_title": "Web Search",
        "search_query": "Search Query",
        "searching": "Searching: {query}",
        "search_results": "Search Results",
        "search_no_results": "No results found",
        "search_error": "Search failed: {error}",
        "search_source": "Source",
        "search_provider": "Search Engine",

        # File handling
        "file_loading": "Loading file: {path}",
        "file_loaded": "File loaded ({size} characters)",
        "file_error": "File processing failed: {error}",
        "file_not_found": "File not found: {path}",
        "file_unsupported": "Unsupported file format: {format}",
        "file_too_large": "File too large ({size} chars), exceeds limit ({limit} chars)",
        "file_content_header": "Below is the content of file {name}:\n\n",

        # Export
        "export_title": "Export Chat",
        "export_success": "Chat exported to {path}",
        "export_error": "Export failed: {error}",
        "export_format": "Export Format",
        "export_no_conversation": "No conversation to export",
        "export_cost_report": "Cost Report",

        # Config
        "config_title": "Current Configuration",
        "config_set_success": "{key} set to {value}",
        "config_set_fail": "Failed to set: {error}",

        # Privacy
        "privacy_detected": "Sensitive information detected:",
        "privacy_masked": "Auto-masked",
        "privacy_level_set": "Privacy level set to {level}",
        "privacy_no_sensitive": "No sensitive information detected",

        # Template
        "template_title": "Prompt Templates",
        "template_not_found": "Template '{name}' not found",
        "template_available": "Available templates:",

        # History
        "history_title": "Chat History",
        "history_empty": "No chat history",

        # Language
        "lang_set": "Language set to {lang}",
        "lang_current": "Current language: {lang}",
        "lang_supported": "Supported languages: zh (Chinese), en (English)",
    },
}


class I18n:
    """多语言管理器"""

    SUPPORTED_LANGUAGES = ("zh", "en")

    def __init__(self):
        self._lang = config.get("language", "zh")

    @property
    def lang(self) -> str:
        """当前语言"""
        return self._lang

    @lang.setter
    def lang(self, value: str) -> None:
        """设置语言"""
        if value not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"不支持的语言: {value}，支持: {', '.join(self.SUPPORTED_LANGUAGES)}")
        self._lang = value
        config.set("language", value)

    def t(self, key: str, **kwargs: Any) -> str:
        """获取翻译文本

        Args:
            key: 翻译键名
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        translations = TRANSLATIONS.get(self._lang, TRANSLATIONS["zh"])
        text = translations.get(key)
        if text is None:
            # 回退到中文
            text = TRANSLATIONS["zh"].get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text

    def get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        names = {"zh": "中文", "en": "English"}
        return names.get(lang_code, lang_code)

    def list_languages(self) -> list[dict[str, str]]:
        """列出支持的语言"""
        return [
            {"code": code, "name": self.get_language_name(code)}
            for code in self.SUPPORTED_LANGUAGES
        ]


# 全局实例
i18n = I18n()
