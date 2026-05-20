"""CLI主程序"""

import asyncio
import io
import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import __version__
from .config import config
from .cost_tracker import cost_tracker
from .export import exporter
from .file_handler import file_handler
from .i18n import i18n
from .privacy import privacy_protector
from .providers.base import Message
from .providers.claude import ClaudeProvider
from .providers.mimo import MiMoProvider
from .providers.ollama import OllamaProvider
from .providers.openai import OpenAIProvider
from .storage import storage
from .templates.manager import TemplateManager
from .web_search import web_searcher


def _setup_windows_encoding():
    """修复Windows中文环境下的编码问题

    核心策略：
    1. 设置环境变量 PYTHONIOENCODING，确保子进程也使用UTF-8
    2. 先切换控制台代码页，再重新配置Python标准流
    3. 使用独立的文件描述符避免与 sys.stdout 状态冲突
    """
    if sys.platform != "win32":
        return

    # 设置环境变量，影响后续所有子进程和 asyncio 的默认编码
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # 切换控制台代码页到UTF-8（65001）
    os.system("chcp 65001 >nul 2>&1")

    # 重新配置标准流编码，errors="replace" 防止不可编码字符导致崩溃
    for stream_name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _create_console() -> Console:
    """创建 Rich Console

    Windows 下直接使用 sys.stdout（已通过 reconfigure 设置 UTF-8），
    不创建额外的 TextIOWrapper，避免文件描述符生命周期冲突。
    """
    if sys.platform == "win32":
        return Console(file=sys.stdout, force_terminal=True)
    return Console()


# 启动时立即修复编码
_setup_windows_encoding()

# 创建 Console 实例
console = _create_console()
template_manager = TemplateManager()


def get_provider(provider_name: Optional[str] = None):
    """获取AI提供商实例"""
    name = provider_name or config.get_default_provider()
    provider_config = config.get_provider_config(name)

    if name == "openai":
        return OpenAIProvider(provider_config)
    elif name == "claude":
        return ClaudeProvider(provider_config)
    elif name == "ollama":
        return OllamaProvider(provider_config)
    elif name == "mimo":
        return MiMoProvider(provider_config)
    else:
        raise ValueError(f"不支持的提供商: {name}")


@click.group()
@click.version_option(version=__version__, prog_name="ai-assistant")
def main():
    """AI Assistant - 本地化AI助手

    解决普通用户使用AI的三大痛点：回答不准、收费贵、隐私顾虑
    """
    pass


@main.command()
@click.option("--provider", "-p", help="AI提供商 (openai/claude/ollama)")
@click.option("--model", "-m", help="模型名称")
@click.option("--template", "-t", help="使用提示词模板")
@click.option("--system", "-s", help="系统提示词")
@click.option("--stream/--no-stream", default=True, help="是否流式输出")
def chat(
    provider: Optional[str],
    model: Optional[str],
    template: Optional[str],
    system: Optional[str],
    stream: bool,
):
    """开始对话"""
    # 获取提供商
    try:
        ai_provider = get_provider(provider)
    except ValueError as e:
        console.print(f"[red]{i18n.t('error')}: {e}[/red]")
        return
    except Exception as e:
        console.print(f"[red]{i18n.t('error')}: {e}[/red]")
        return

    # 处理模板
    template_obj = None
    if template:
        template_obj = template_manager.get_template(template)
        if not template_obj:
            console.print(f"[red]{i18n.t('template_not_found', name=template)}[/red]")
            console.print(i18n.t("template_available"))
            for t in template_manager.list_templates():
                console.print(f"  - {t['name']}: {t['description']}")
            return

    # 初始化对话
    messages = []
    if system:
        messages.append(Message(role="system", content=system))
    elif template_obj:
        messages.append(Message(role="system", content=template_obj.get_system_prompt()))

    # 创建对话记录
    provider_name = provider or config.get_default_provider()
    model_name = model or config.get_provider_config(provider_name).get("model", "unknown")
    conversation_id = storage.create_conversation(
        title=f"对话 {len(storage.list_conversations()) + 1}",
        provider=provider_name,
        model=model_name,
    )

    # 额外上下文（搜索结果、文件内容等）
    extra_context: list[str] = []

    console.print(Panel(
        f"[bold green]{i18n.t('app_name')}[/bold green]\n"
        f"{i18n.t('chat_provider')}: {provider_name} | {i18n.t('chat_model')}: {model_name}\n"
        f"{i18n.t('chat_privacy_level')}: {privacy_protector.get_level_description()}\n\n"
        f"{i18n.t('chat_start')}",
        title=i18n.t("welcome"),
    ))

    if template_obj:
        console.print(f"[dim]{i18n.t('chat_using_template')}: {template_obj.description}[/dim]")
        if template_obj.variables:
            console.print(f"[dim]{i18n.t('chat_template_hint')}[/dim]")

    # 对话循环
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]你[/bold cyan]")

            # 处理命令
            if user_input.lower() in ("quit", "exit", "q"):
                console.print(f"[yellow]{i18n.t('goodbye')}[/yellow]")
                break

            if user_input.lower() == "help":
                _show_help()
                continue

            if user_input.lower() == "cost":
                cost_tracker.display_stats()
                continue

            if user_input.lower() == "tips":
                tips = cost_tracker.get_optimization_tips()
                console.print(f"[bold]{i18n.t('cost_optimization')}：[/bold]")
                for tip in tips:
                    console.print(f"  - {tip}")
                continue

            # 联网搜索命令
            if user_input.lower().startswith("/search "):
                query = user_input[8:].strip()
                if query:
                    _handle_search(query, messages, extra_context)
                continue

            # 文件加载命令
            if user_input.lower().startswith("/file "):
                file_path = user_input[6:].strip()
                if file_path:
                    _handle_file(file_path, messages, extra_context)
                continue

            # 导出命令
            if user_input.lower().startswith("/export "):
                fmt = user_input[8:].strip()
                if fmt:
                    _handle_export(conversation_id, fmt)
                continue

            if not user_input.strip():
                continue

            # 隐私检查
            safe_input = privacy_protector.get_safe_input(user_input)

            # 添加用户消息
            user_message = Message(role="user", content=safe_input)
            messages.append(user_message)
            storage.add_message(conversation_id, "user", safe_input)

            # 调用AI
            console.print(f"\n[bold green]AI[/bold green]: ", end="")

            if stream:
                response = asyncio.run(_stream_response(ai_provider, messages, model))
            else:
                response = asyncio.run(_get_response(ai_provider, messages, model))

            if response:
                # 记录成本
                cost = ai_provider.calculate_cost(response.usage, response.model)
                cost_tracker.record(
                    provider=response.provider,
                    model=response.model,
                    usage=response.usage,
                    cost=cost,
                )

                # 存储响应
                storage.add_message(
                    conversation_id,
                    "assistant",
                    response.content,
                    tokens=response.usage.total_tokens,
                    cost=cost,
                )

                # 显示token使用情况
                console.print(
                    f"\n[dim]Token: {response.usage.total_tokens} | "
                    f"Cost: ${cost:.6f}[/dim]"
                )

        except KeyboardInterrupt:
            console.print(f"\n[yellow]{i18n.t('chat_interrupted')}[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]{i18n.t('error')}: {e}[/red]")


def _handle_search(query: str, messages: list, extra_context: list[str]) -> None:
    """处理搜索命令"""
    console.print(f"[dim]{i18n.t('searching', query=query)}[/dim]")
    response = asyncio.run(web_searcher.search(query))

    if response.error:
        console.print(f"[red]{i18n.t('search_error', error=response.error)}[/red]")
        return

    if not response.results:
        console.print(f"[yellow]{i18n.t('search_no_results')}[/yellow]")
        return

    # 显示结果
    formatted = web_searcher.format_results(response)
    console.print(Panel(formatted, title=i18n.t("search_title")))

    # 将搜索结果注入上下文
    context_prompt = web_searcher.get_context_prompt(response)
    if context_prompt:
        extra_context.append(context_prompt)
        # 添加到消息列表作为系统上下文
        messages.append(Message(role="system", content=context_prompt))
        console.print("[dim]搜索结果已添加到对话上下文[/dim]")


def _handle_file(file_path: str, messages: list, extra_context: list[str]) -> None:
    """处理文件加载命令"""
    console.print(f"[dim]{i18n.t('file_loading', path=file_path)}[/dim]")
    file_content = file_handler.load_file(file_path)

    if file_content.error:
        console.print(f"[red]{file_content.error}[/red]")
        return

    # 显示文件信息
    console.print(
        f"[green]{i18n.t('file_loaded', size=file_content.size)}[/green] "
        f"({file_content.format})"
    )

    # 将文件内容注入上下文
    context_prompt = file_handler.get_context_prompt(file_content)
    extra_context.append(context_prompt)
    messages.append(Message(role="system", content=context_prompt))
    console.print("[dim]文件内容已添加到对话上下文[/dim]")


def _handle_export(conversation_id: int, fmt: str) -> None:
    """处理导出命令"""
    try:
        output_path = exporter.export_conversation(conversation_id, fmt)
        console.print(f"[green]{i18n.t('export_success', path=output_path)}[/green]")
    except Exception as e:
        console.print(f"[red]{i18n.t('export_error', error=str(e))}[/red]")


async def _get_response(provider, messages, model):
    """获取AI响应"""
    return await provider.chat(messages, model=model)


async def _stream_response(provider, messages, model):
    """流式获取AI响应"""
    full_response = ""
    async for chunk in provider.chat_stream(messages, model=model):
        console.print(chunk, end="")
        full_response += chunk
    console.print()  # 换行

    # 构造响应对象（流式模式下需要手动构造）
    from .providers.base import ChatResponse, Usage
    return ChatResponse(
        content=full_response,
        model=provider.get_model(model),
        usage=Usage(),  # 流式模式下token数需要从最后的chunk获取
        provider=provider.name,
    )


def _show_help():
    """显示帮助信息"""
    table = Table(title=i18n.t("help_title"))
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")

    table.add_row("quit/exit/q", i18n.t("help_quit"))
    table.add_row("cost", i18n.t("help_cost"))
    table.add_row("tips", i18n.t("help_tips"))
    table.add_row("help", i18n.t("help_help"))
    table.add_row("/search <query>", i18n.t("help_search"))
    table.add_row("/file <path>", i18n.t("help_file"))
    table.add_row("/export <format>", i18n.t("help_export"))

    console.print(table)


# ========== 配置管理 ==========

@main.group()
def config_cmd():
    """配置管理"""
    pass


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置配置值"""
    try:
        if key.endswith("_api_key"):
            provider = key.replace("_api_key", "")
            config.set_api_key(provider, value)
            console.print(f"[green]{provider} API密钥已设置[/green]")
        elif key == "default_provider":
            config.set_default_provider(value)
            console.print(f"[green]默认提供商已设置为 {value}[/green]")
        elif key == "privacy_level":
            config.set_privacy_level(value)
            console.print(f"[green]隐私级别已设置为 {value}[/green]")
        elif key == "budget_alert":
            config.set_budget_alert(float(value))
            console.print(f"[green]预算警报已设置为 ${value}[/green]")
        elif key == "language":
            i18n.lang = value
            console.print(f"[green]{i18n.t('lang_set', lang=value)}[/green]")
        else:
            config.set(key, value)
            console.print(f"[green]{i18n.t('config_set_success', key=key, value=value)}[/green]")
    except Exception as e:
        console.print(f"[red]{i18n.t('config_set_fail', error=str(e))}[/red]")


@config_cmd.command("show")
def config_show():
    """显示当前配置"""
    table = Table(title=i18n.t("config_title"))
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    current_config = config.show()
    _flatten_config(current_config, "", table)

    console.print(table)


def _flatten_config(data, prefix, table):
    """递归展开配置"""
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            _flatten_config(value, full_key, table)
        else:
            table.add_row(full_key, str(value))


# ========== 成本管理 ==========

@main.group()
def cost():
    """成本管理"""
    pass


@cost.command("stats")
@click.option("--start", help="开始日期 (YYYY-MM-DD)")
@click.option("--end", help="结束日期 (YYYY-MM-DD)")
def cost_stats(start: Optional[str], end: Optional[str]):
    """显示成本统计"""
    stats = cost_tracker.get_stats(start, end)
    cost_tracker.display_stats(stats)


@cost.command("tips")
def cost_tips():
    """显示成本优化建议"""
    tips = cost_tracker.get_optimization_tips()
    console.print(f"[bold]{i18n.t('cost_optimization')}：[/bold]")
    for tip in tips:
        console.print(f"  - {tip}")


@cost.command("export")
@click.argument("file_path")
@click.option("--start", help="开始日期 (YYYY-MM-DD)")
def cost_export(file_path: str, start: Optional[str]):
    """导出成本记录"""
    cost_tracker.export_csv(file_path, start)


# ========== 模板管理 ==========

@main.group()
def template():
    """模板管理"""
    pass


@template.command("list")
@click.option("--category", "-c", help="按分类筛选")
def template_list(category: Optional[str]):
    """列出模板"""
    templates = template_manager.list_templates(category)

    table = Table(title=i18n.t("template_title"))
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Tags", style="dim")

    for t in templates:
        table.add_row(t["name"], t["description"], t["category"], t["tags"])

    console.print(table)


@template.command("show")
@click.argument("name")
def template_show(name: str):
    """显示模板详情"""
    t = template_manager.get_template(name)
    if not t:
        console.print(f"[red]{i18n.t('template_not_found', name=name)}[/red]")
        return

    console.print(Panel(
        f"[bold]{t.description}[/bold]\n\n"
        f"Category: {t.category}\n"
        f"Tags: {', '.join(t.tags)}\n\n"
        f"[cyan]System Prompt:[/cyan]\n{t.system_prompt}\n\n"
        f"[cyan]User Prompt Template:[/cyan]\n{t.user_prompt_template}\n\n"
        f"[cyan]Variables:[/cyan]{', '.join(t.variables) if t.variables else 'None'}",
        title=f"Template: {name}",
    ))


# ========== 隐私管理 ==========

@main.group()
def privacy():
    """隐私管理"""
    pass


@privacy.command("level")
@click.argument("level", type=click.Choice(["low", "medium", "high"]))
def privacy_level(level: str):
    """设置隐私级别"""
    privacy_protector.set_level(level)


@privacy.command("test")
@click.argument("text")
def privacy_test(text: str):
    """测试隐私检测"""
    has_sensitive, results = privacy_protector.check_and_warn(text)
    if has_sensitive:
        console.print(f"\n[bold]脱敏结果：[/bold]")
        console.print(privacy_protector.mask(text))
    else:
        console.print(f"[green]{i18n.t('privacy_no_sensitive')}[/green]")


# ========== 对话历史 ==========

@main.command()
def history():
    """查看对话历史"""
    conversations = storage.list_conversations(20)

    if not conversations:
        console.print(f"[dim]{i18n.t('history_empty')}[/dim]")
        return

    table = Table(title=i18n.t("history_title"))
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Provider", style="yellow")
    table.add_column("Model", style="yellow")
    table.add_column("Updated", style="dim")

    for conv in conversations:
        table.add_row(
            str(conv["id"]),
            conv["title"],
            conv["provider"],
            conv["model"],
            conv["updated_at"],
        )

    console.print(table)


# ========== 联网搜索 ==========

@main.command()
@click.argument("query")
@click.option("--provider", "-p", help="搜索引擎 (duckduckgo/bing)")
@click.option("--max-results", "-n", default=5, help="最大结果数")
def search(query: str, provider: Optional[str], max_results: int):
    """联网搜索"""
    console.print(f"[dim]{i18n.t('searching', query=query)}[/dim]")
    response = asyncio.run(web_searcher.search(query, max_results, provider))

    if response.error:
        console.print(f"[red]{i18n.t('search_error', error=response.error)}[/red]")
        return

    if not response.results:
        console.print(f"[yellow]{i18n.t('search_no_results')}[/yellow]")
        return

    formatted = web_searcher.format_results(response)
    console.print(Panel(formatted, title=i18n.t("search_title")))


# ========== 文件处理 ==========

@main.command()
@click.argument("file_path")
def file_info(file_path: str):
    """查看文件信息"""
    file_content = file_handler.load_file(file_path)

    if file_content.error:
        console.print(f"[red]{file_content.error}[/red]")
        return

    table = Table(title="File Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Path", file_content.path)
    table.add_row("Name", file_content.name)
    table.add_row("Format", file_content.format)
    table.add_row("Size", f"{file_content.size:,} characters")
    table.add_row("Supported", "Yes" if file_handler.is_supported(file_path) else "No")

    console.print(table)

    # 显示内容预览
    preview = file_content.content[:500]
    if len(file_content.content) > 500:
        preview += "\n..."
    console.print(Panel(preview, title="Content Preview"))


# ========== 导出 ==========

@main.group()
def export():
    """导出管理"""
    pass


@export.command("chat")
@click.argument("conversation_id", type=int)
@click.option("--format", "-f", "fmt", default="md",
              type=click.Choice(["md", "html", "pdf", "txt"]),
              help="导出格式")
@click.option("--output", "-o", help="输出路径")
def export_chat(conversation_id: int, fmt: str, output: Optional[str]):
    """导出对话"""
    try:
        output_path = exporter.export_conversation(conversation_id, fmt, output)
        console.print(f"[green]{i18n.t('export_success', path=output_path)}[/green]")
    except Exception as e:
        console.print(f"[red]{i18n.t('export_error', error=str(e))}[/red]")


@export.command("cost")
@click.option("--format", "-f", "fmt", default="md",
              type=click.Choice(["md", "html", "txt"]),
              help="导出格式")
@click.option("--output", "-o", help="输出路径")
@click.option("--start", help="开始日期 (YYYY-MM-DD)")
@click.option("--end", help="结束日期 (YYYY-MM-DD)")
def export_cost(fmt: str, output: Optional[str], start: Optional[str], end: Optional[str]):
    """导出成本报告"""
    try:
        output_path = exporter.export_cost_report(fmt, output, start, end)
        console.print(f"[green]{i18n.t('export_success', path=output_path)}[/green]")
    except Exception as e:
        console.print(f"[red]{i18n.t('export_error', error=str(e))}[/red]")


# ========== 多语言 ==========

@main.command()
@click.argument("lang", required=False)
def language(lang: Optional[str]):
    """查看或设置语言 (zh/en)"""
    if lang:
        try:
            i18n.lang = lang
            console.print(f"[green]{i18n.t('lang_set', lang=lang)}[/green]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
    else:
        console.print(f"[cyan]{i18n.t('lang_current', lang=i18n.lang)}[/cyan]")
        console.print(f"[dim]{i18n.t('lang_supported')}[/dim]")


# ========== GUI ==========

@main.command()
def gui():
    """启动图形界面"""
    try:
        from .gui import run_gui
        run_gui()
    except ImportError:
        console.print("[red]错误: 请安装PyQt6依赖[/red]")
        console.print("[yellow]运行: pip install 'ai-assistant[gui]'[/yellow]")


if __name__ == "__main__":
    main()
