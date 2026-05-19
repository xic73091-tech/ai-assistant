"""隐私保护模块"""

import re
from dataclasses import dataclass
from typing import Optional

from rich.console import Console

from .config import config

console = Console()


@dataclass
class SensitiveInfo:
    """敏感信息"""
    type: str  # 类型：id_card, phone, email, bank_card, password
    value: str  # 原始值
    masked: str  # 脱敏后的值
    position: tuple[int, int]  # 在原文中的位置


class PrivacyProtector:
    """隐私保护器"""

    # 敏感信息正则表达式
    PATTERNS = {
        "id_card": {
            "pattern": r"(?<!\d)\d{17}[\dXx](?!\d)",
            "description": "身份证号",
            "mask": lambda m: m[:6] + "********" + m[-4:],
        },
        "phone": {
            "pattern": r"(?<!\d)1[3-9]\d{9}(?!\d)",
            "description": "手机号",
            "mask": lambda m: m[:3] + "****" + m[-4:],
        },
        "email": {
            "pattern": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}",
            "description": "邮箱",
            "mask": lambda m: m[:3] + "***@" + m.split("@")[1],
        },
        "bank_card": {
            "pattern": r"(?<!\d)\d{16,19}(?!\d)",
            "description": "银行卡号",
            "mask": lambda m: m[:4] + " **** **** " + m[-4:],
        },
        "password": {
            "pattern": r"(?i)(password|passwd|pwd|密码)[：:]\s*\S+",
            "description": "密码",
            "mask": lambda m: m.split(":")[0] + ": ********" if ":" in m else "密码: ********",
        },
        "ip_address": {
            "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "description": "IP地址",
            "mask": lambda m: m[:m.rfind(".")] + ".***",
        },
    }

    def __init__(self, level: Optional[str] = None):
        self.level = level or config.get_privacy_level()
        self.enabled_levels = self._get_enabled_levels()

    def _get_enabled_levels(self) -> list[str]:
        """根据隐私级别启用检测项"""
        if self.level == "high":
            return list(self.PATTERNS.keys())
        elif self.level == "medium":
            return ["id_card", "phone", "bank_card", "password"]
        else:  # low
            return ["id_card", "bank_card", "password"]

    def detect(self, text: str) -> list[SensitiveInfo]:
        """检测敏感信息"""
        results = []
        for info_type in self.enabled_levels:
            pattern_info = self.PATTERNS[info_type]
            for match in re.finditer(pattern_info["pattern"], text):
                value = match.group()
                # 排除明显不是敏感信息的匹配
                if self._is_false_positive(info_type, value):
                    continue
                masked = pattern_info["mask"](value)
                results.append(SensitiveInfo(
                    type=info_type,
                    value=value,
                    masked=masked,
                    position=(match.start(), match.end()),
                ))
        return results

    def _is_false_positive(self, info_type: str, value: str) -> bool:
        """判断是否为误报"""
        if info_type == "bank_card":
            # 排除明显不是银行卡号的数字
            if len(value) < 16 or len(value) > 19:
                return True
            # 排除纯0
            if value == "0" * len(value):
                return True
        if info_type == "ip_address":
            # 验证IP地址格式
            parts = value.split(".")
            for part in parts:
                if int(part) > 255:
                    return True
        return False

    def mask(self, text: str) -> str:
        """对文本进行脱敏处理"""
        if self.level == "low":
            return text

        results = self.detect(text)
        if not results:
            return text

        # 从后往前替换，避免位置偏移
        masked_text = text
        for info in sorted(results, key=lambda x: x.position[0], reverse=True):
            start, end = info.position
            masked_text = masked_text[:start] + info.masked + masked_text[end:]

        return masked_text

    def check_and_warn(self, text: str) -> tuple[bool, list[SensitiveInfo]]:
        """检查并警告敏感信息"""
        results = self.detect(text)
        if results:
            console.print("[bold yellow][!] 检测到敏感信息：[/bold yellow]")
            for info in results:
                desc = self.PATTERNS[info.type]["description"]
                console.print(f"  - {desc}: {info.masked}")
            return True, results
        return False, results

    def get_safe_input(self, text: str) -> str:
        """获取安全的输入（脱敏后）"""
        has_sensitive, results = self.check_and_warn(text)
        if has_sensitive:
            console.print("[dim]已自动脱敏处理[/dim]")
            return self.mask(text)
        return text

    def set_level(self, level: str) -> None:
        """设置隐私级别"""
        if level not in ("low", "medium", "high"):
            raise ValueError("隐私级别必须是 low, medium 或 high")
        self.level = level
        self.enabled_levels = self._get_enabled_levels()
        config.set_privacy_level(level)
        console.print(f"[green]隐私保护级别已设置为 {level}[/green]")

    def get_level_description(self) -> str:
        """获取当前级别的描述"""
        descriptions = {
            "low": "低：仅检测身份证号、银行卡号和密码",
            "medium": "中：检测身份证号、手机号、银行卡号和密码",
            "high": "高：检测所有敏感信息（身份证、手机、邮箱、银行卡、密码、IP地址）",
        }
        return descriptions.get(self.level, "未知级别")


# 全局隐私保护器实例
privacy_protector = PrivacyProtector()
