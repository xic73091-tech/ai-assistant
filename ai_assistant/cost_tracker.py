"""成本追踪模块"""

import sys
from datetime import datetime
from typing import Any, Optional

from rich.console import Console
from rich.table import Table

from .config import config
from .providers.base import Usage
from .storage import storage

console = Console(file=sys.stdout, force_terminal=True) if sys.platform == "win32" else Console()


class CostTracker:
    """成本追踪器"""

    def __init__(self):
        self.budget_alert = config.get_budget_alert()

    def record(
        self,
        provider: str,
        model: str,
        usage: Usage,
        cost: float,
    ) -> None:
        """记录一次调用成本"""
        storage.add_cost_record(
            provider=provider,
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost=cost,
        )

        # 检查预算警报
        self._check_budget_alert()

    def _check_budget_alert(self) -> None:
        """检查预算警报"""
        recent_cost = storage.get_recent_cost(days=30)
        if recent_cost >= self.budget_alert:
            console.print(
                f"[bold yellow][!] 警告：本月已花费 ${recent_cost:.2f}，"
                f"超过预算阈值 ${self.budget_alert:.2f}[/bold yellow]"
            )

    def get_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """获取成本统计"""
        return storage.get_cost_stats(start_date=start_date, end_date=end_date)

    def get_monthly_summary(self) -> dict[str, Any]:
        """获取本月摘要"""
        now = datetime.now()
        start_date = now.strftime("%Y-%m-01")
        return self.get_stats(start_date=start_date)

    def display_stats(self, stats: Optional[dict[str, Any]] = None) -> None:
        """显示成本统计"""
        if stats is None:
            stats = self.get_stats()

        # 总览表格
        table = Table(title="成本统计总览")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="green")

        table.add_row("总花费", f"${stats['total_cost']:.4f}")
        table.add_row("总Token数", f"{stats['total_tokens']:,}")
        table.add_row("记录数", f"{stats['record_count']:,}")

        console.print(table)

        # 按提供商统计
        if stats["by_provider"]:
            provider_table = Table(title="按提供商统计")
            provider_table.add_column("提供商", style="cyan")
            provider_table.add_column("花费", style="green")

            for provider, cost in sorted(
                stats["by_provider"].items(), key=lambda x: x[1], reverse=True
            ):
                provider_table.add_row(provider, f"${cost:.4f}")

            console.print(provider_table)

        # 按模型统计
        if stats["by_model"]:
            model_table = Table(title="按模型统计")
            model_table.add_column("模型", style="cyan")
            model_table.add_column("花费", style="green")

            for model, cost in sorted(
                stats["by_model"].items(), key=lambda x: x[1], reverse=True
            ):
                model_table.add_row(model, f"${cost:.4f}")

            console.print(model_table)

    def get_optimization_tips(self) -> list[str]:
        """获取成本优化建议"""
        tips = []
        stats = self.get_stats()

        if not stats["by_model"]:
            return ["暂无使用记录，无法提供优化建议"]

        # 找出最贵的模型
        most_expensive_model = max(stats["by_model"].items(), key=lambda x: x[1])
        if most_expensive_model[1] > 1.0:
            tips.append(
                f"模型 {most_expensive_model[0]} 花费最高 "
                f"(${most_expensive_model[1]:.2f})，考虑对简单任务使用更便宜的模型"
            )

        # 检查是否可以使用本地模型
        if "ollama" not in stats["by_provider"]:
            tips.append("未使用本地模型，对于非关键任务可以考虑使用Ollama降低成本")

        # 检查token使用效率
        if stats["total_tokens"] > 0:
            avg_cost_per_token = stats["total_cost"] / stats["total_tokens"]
            if avg_cost_per_token > 0.00003:
                tips.append("平均token成本较高，考虑优化提示词减少不必要的token消耗")

        # 预算建议
        monthly_cost = self.get_monthly_summary()["total_cost"]
        if monthly_cost > 0:
            tips.append(f"本月已花费 ${monthly_cost:.2f}，建议设置合理的月度预算")

        return tips if tips else ["当前使用情况良好，暂无优化建议"]

    def set_budget_alert(self, amount: float) -> None:
        """设置预算警报阈值"""
        self.budget_alert = amount
        config.set_budget_alert(amount)
        console.print(f"[green]预算警报阈值已设置为 ${amount:.2f}[/green]")

    def export_csv(self, file_path: str, start_date: Optional[str] = None) -> None:
        """导出成本记录为CSV"""
        import csv

        stats = self.get_stats(start_date=start_date)
        # 这里简化处理，实际应该查询原始记录
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["提供商", "模型", "花费"])
            for provider, cost in stats["by_provider"].items():
                writer.writerow([provider, "", f"{cost:.4f}"])
            for model, cost in stats["by_model"].items():
                writer.writerow(["", model, f"{cost:.4f}"])

        console.print(f"[green]成本记录已导出到 {file_path}[/green]")


# 全局成本追踪器实例
cost_tracker = CostTracker()
