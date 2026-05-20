"""对话导出模块"""

import html as html_module
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .cost_tracker import cost_tracker
from .i18n import i18n
from .storage import storage


class Exporter:
    """对话导出器"""

    SUPPORTED_FORMATS = ("md", "markdown", "html", "pdf", "txt")

    def export_conversation(
        self,
        conversation_id: int,
        output_format: str = "md",
        output_path: Optional[str] = None,
    ) -> str:
        """导出对话

        Args:
            conversation_id: 对话ID
            output_format: 输出格式 (md/markdown, html, pdf, txt)
            output_path: 输出路径（可选）

        Returns:
            导出文件路径
        """
        conversation = storage.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(i18n.t("export_no_conversation"))

        messages = storage.get_conversation_messages(conversation_id)

        fmt = output_format.lower()
        if fmt in ("md", "markdown"):
            content = self._to_markdown(conversation, messages)
            ext = ".md"
        elif fmt == "html":
            content = self._to_html(conversation, messages)
            ext = ".html"
        elif fmt == "pdf":
            content = self._to_html(conversation, messages)
            ext = ".pdf"
        elif fmt == "txt":
            content = self._to_text(conversation, messages)
            ext = ".txt"
        else:
            raise ValueError(f"Unsupported format: {output_format}")

        # 确定输出路径
        if output_path:
            file_path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(
                c for c in conversation.get("title", "chat")
                if c.isalnum() or c in (" ", "-", "_")
            ).strip()[:50]
            file_path = Path(f"{safe_title}_{timestamp}{ext}")

        # PDF需要额外处理
        if fmt == "pdf":
            self._write_pdf(content, file_path)
        else:
            file_path.write_text(content, encoding="utf-8")

        return str(file_path)

    def export_cost_report(
        self,
        output_format: str = "md",
        output_path: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """导出成本报告

        Args:
            output_format: 输出格式
            output_path: 输出路径
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            导出文件路径
        """
        stats = cost_tracker.get_stats(start_date, end_date)

        fmt = output_format.lower()
        if fmt in ("md", "markdown"):
            content = self._cost_to_markdown(stats)
            ext = ".md"
        elif fmt == "html":
            content = self._cost_to_html(stats)
            ext = ".html"
        elif fmt == "txt":
            content = self._cost_to_text(stats)
            ext = ".txt"
        else:
            raise ValueError(f"Unsupported format: {output_format}")

        if output_path:
            file_path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = Path(f"cost_report_{timestamp}{ext}")

        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def _to_markdown(self, conversation: dict, messages: list[dict]) -> str:
        """转为Markdown格式"""
        lines = []
        lines.append(f"# {conversation.get('title', 'Chat')}\n")
        lines.append(f"- **Provider**: {conversation.get('provider', 'N/A')}")
        lines.append(f"- **Model**: {conversation.get('model', 'N/A')}")
        lines.append(f"- **Created**: {conversation.get('created_at', 'N/A')}")
        lines.append(f"- **Updated**: {conversation.get('updated_at', 'N/A')}")
        lines.append("")
        lines.append("---\n")

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tokens = msg.get("tokens", 0)
            cost = msg.get("cost", 0.0)
            created = msg.get("created_at", "")

            if role == "user":
                lines.append(f"## User\n")
                lines.append(content)
            elif role == "assistant":
                lines.append(f"\n## Assistant\n")
                lines.append(content)
            elif role == "system":
                lines.append(f"\n## System\n")
                lines.append(f"_{content}_")

            meta = []
            if tokens:
                meta.append(f"Tokens: {tokens}")
            if cost:
                meta.append(f"Cost: ${cost:.6f}")
            if created:
                meta.append(f"Time: {created}")
            if meta:
                lines.append(f"\n_{', '.join(meta)}_")
            lines.append("")

        return "\n".join(lines)

    def _to_html(self, conversation: dict, messages: list[dict]) -> str:
        """转为HTML格式"""
        title = html_module.escape(conversation.get("title", "Chat"))
        provider = html_module.escape(conversation.get("provider", "N/A"))
        model = html_module.escape(conversation.get("model", "N/A"))
        created = html_module.escape(str(conversation.get("created_at", "N/A")))

        parts = [
            "<!DOCTYPE html>",
            "<html lang='zh'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; "
            "max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }",
            ".message { margin: 15px 0; padding: 15px; border-radius: 8px; }",
            ".user { background: #e3f2fd; border-left: 4px solid #2196f3; }",
            ".assistant { background: #f3e5f5; border-left: 4px solid #9c27b0; }",
            ".system { background: #fff3e0; border-left: 4px solid #ff9800; font-style: italic; }",
            ".meta { font-size: 0.85em; color: #666; margin-top: 8px; }",
            ".header { background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }",
            "h1 { color: #333; }",
            "pre { white-space: pre-wrap; word-wrap: break-word; }",
            "</style>",
            "</head>",
            "<body>",
            f"<div class='header'>",
            f"<h1>{title}</h1>",
            f"<p><strong>Provider:</strong> {provider} | <strong>Model:</strong> {model}</p>",
            f"<p><strong>Created:</strong> {created}</p>",
            "</div>",
        ]

        for msg in messages:
            role = html_module.escape(msg.get("role", "unknown"))
            content = html_module.escape(msg.get("content", ""))
            tokens = msg.get("tokens", 0)
            cost = msg.get("cost", 0.0)

            role_label = {"user": "User", "assistant": "Assistant", "system": "System"}.get(role, role)

            parts.append(f"<div class='message {role}'>")
            parts.append(f"<strong>{role_label}</strong>")
            parts.append(f"<pre>{content}</pre>")
            if tokens or cost:
                parts.append(f"<div class='meta'>Tokens: {tokens}, Cost: ${cost:.6f}</div>")
            parts.append("</div>")

        parts.extend(["</body>", "</html>"])
        return "\n".join(parts)

    def _to_text(self, conversation: dict, messages: list[dict]) -> str:
        """转为纯文本格式"""
        lines = []
        lines.append(conversation.get("title", "Chat"))
        lines.append("=" * 60)
        lines.append(f"Provider: {conversation.get('provider', 'N/A')}")
        lines.append(f"Model: {conversation.get('model', 'N/A')}")
        lines.append(f"Created: {conversation.get('created_at', 'N/A')}")
        lines.append("")
        lines.append("-" * 60)

        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            lines.append(f"\n[{role}]")
            lines.append(content)
            lines.append("")

        return "\n".join(lines)

    def _cost_to_markdown(self, stats: dict[str, Any]) -> str:
        """成本报告转Markdown"""
        lines = []
        lines.append(f"# {i18n.t('export_cost_report')}\n")
        lines.append(f"**{i18n.t('cost_total')}**: ${stats['total_cost']:.4f}")
        lines.append(f"**{i18n.t('cost_tokens')}**: {stats['total_tokens']:,}")
        lines.append(f"**{i18n.t('cost_records')}**: {stats['record_count']:,}")
        lines.append("")

        if stats["by_provider"]:
            lines.append(f"## {i18n.t('cost_by_provider')}\n")
            lines.append("| Provider | Cost |")
            lines.append("|----------|------|")
            for provider, cost in sorted(
                stats["by_provider"].items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"| {provider} | ${cost:.4f} |")
            lines.append("")

        if stats["by_model"]:
            lines.append(f"## {i18n.t('cost_by_model')}\n")
            lines.append("| Model | Cost |")
            lines.append("|-------|------|")
            for model, cost in sorted(
                stats["by_model"].items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"| {model} | ${cost:.4f} |")

        return "\n".join(lines)

    def _cost_to_html(self, stats: dict[str, Any]) -> str:
        """成本报告转HTML"""
        total = f"${stats['total_cost']:.4f}"
        tokens = f"{stats['total_tokens']:,}"
        records = f"{stats['record_count']:,}"

        parts = [
            "<!DOCTYPE html>",
            "<html lang='zh'>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{i18n.t('export_cost_report')}</title>",
            "<style>",
            "body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background: #f5f5f5; }",
            ".summary { display: flex; gap: 20px; margin: 20px 0; }",
            ".card { background: #f9f9f9; padding: 15px; border-radius: 8px; flex: 1; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{i18n.t('export_cost_report')}</h1>",
            "<div class='summary'>",
            f"<div class='card'><strong>{i18n.t('cost_total')}</strong><br>{total}</div>",
            f"<div class='card'><strong>{i18n.t('cost_tokens')}</strong><br>{tokens}</div>",
            f"<div class='card'><strong>{i18n.t('cost_records')}</strong><br>{records}</div>",
            "</div>",
        ]

        if stats["by_provider"]:
            parts.append(f"<h2>{i18n.t('cost_by_provider')}</h2>")
            parts.append("<table><tr><th>Provider</th><th>Cost</th></tr>")
            for provider, cost in sorted(
                stats["by_provider"].items(), key=lambda x: x[1], reverse=True
            ):
                parts.append(f"<tr><td>{html_module.escape(provider)}</td><td>${cost:.4f}</td></tr>")
            parts.append("</table>")

        if stats["by_model"]:
            parts.append(f"<h2>{i18n.t('cost_by_model')}</h2>")
            parts.append("<table><tr><th>Model</th><th>Cost</th></tr>")
            for model, cost in sorted(
                stats["by_model"].items(), key=lambda x: x[1], reverse=True
            ):
                parts.append(f"<tr><td>{html_module.escape(model)}</td><td>${cost:.4f}</td></tr>")
            parts.append("</table>")

        parts.extend(["</body>", "</html>"])
        return "\n".join(parts)

    def _cost_to_text(self, stats: dict[str, Any]) -> str:
        """成本报告转纯文本"""
        lines = []
        lines.append(i18n.t("export_cost_report"))
        lines.append("=" * 40)
        lines.append(f"{i18n.t('cost_total')}: ${stats['total_cost']:.4f}")
        lines.append(f"{i18n.t('cost_tokens')}: {stats['total_tokens']:,}")
        lines.append(f"{i18n.t('cost_records')}: {stats['record_count']:,}")
        lines.append("")

        if stats["by_provider"]:
            lines.append(i18n.t("cost_by_provider"))
            lines.append("-" * 30)
            for provider, cost in sorted(
                stats["by_provider"].items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"  {provider}: ${cost:.4f}")
            lines.append("")

        if stats["by_model"]:
            lines.append(i18n.t("cost_by_model"))
            lines.append("-" * 30)
            for model, cost in sorted(
                stats["by_model"].items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"  {model}: ${cost:.4f}")

        return "\n".join(lines)

    def _write_pdf(self, html_content: str, file_path: Path) -> None:
        """写入PDF文件"""
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(str(file_path))
        except ImportError:
            # 回退：用html文件替代，并提示安装依赖
            fallback = file_path.with_suffix(".html")
            fallback.write_text(html_content, encoding="utf-8")
            raise ValueError(
                f"PDF export requires weasyprint. HTML saved to {fallback}. "
                "Install with: pip install weasyprint"
            )


# 全局实例
exporter = Exporter()
