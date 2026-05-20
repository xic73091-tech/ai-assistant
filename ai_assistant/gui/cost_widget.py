"""成本统计界面"""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..cost_tracker import cost_tracker
from ..storage import storage
from .styles import (
    get_current_theme,
    get_card_stylesheet,
    get_label_color,
    get_primary_button_stylesheet,
    get_chart_colors,
    Theme,
)


# ============ 图表组件 ============

class BarChartWidget(QWidget):
    """基于QPainter的柱状图组件，无需额外依赖"""

    def __init__(self, data: dict[str, float] = None, title: str = "", parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.title = title
        self.setMinimumHeight(220)
        self.setMinimumWidth(300)

    def update_data(self, data: dict[str, float]) -> None:
        """更新图表数据"""
        self.data = data
        self.update()

    def set_title(self, title: str) -> None:
        """设置图表标题"""
        self.title = title
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        theme = get_current_theme()
        colors = get_chart_colors()

        # 边距
        left_margin = 70
        right_margin = 20
        top_margin = 40
        bottom_margin = 45

        chart_x = left_margin
        chart_y = top_margin
        chart_w = w - left_margin - right_margin
        chart_h = h - top_margin - bottom_margin

        if chart_w <= 0 or chart_h <= 0:
            painter.end()
            return

        # 标题
        if self.title:
            title_color = QColor(get_label_color(theme))
            painter.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
            painter.setPen(title_color)
            painter.drawText(0, 5, w, 30, Qt.AlignmentFlag.AlignCenter, self.title)

        n = len(self.data)
        if n == 0:
            painter.end()
            return

        # 计算柱宽
        bar_gap = 8
        bar_w = max(20, min(80, (chart_w - (n + 1) * bar_gap) // n))
        total_bars_w = n * bar_w + (n - 1) * bar_gap
        start_x = chart_x + (chart_w - total_bars_w) // 2

        max_val = max(self.data.values()) if self.data else 1
        if max_val == 0:
            max_val = 1

        # 网格线
        grid_color = QColor("#3E3E3E" if theme == Theme.DARK else "#E0E0E0")
        painter.setPen(grid_color)
        for i in range(5):
            y = chart_y + int(chart_h * i / 4)
            painter.drawLine(chart_x, y, chart_x + chart_w, y)

        # Y轴标签
        text_color = QColor(get_label_color(theme, secondary=True))
        painter.setPen(text_color)
        painter.setFont(QFont("Microsoft YaHei", 9))
        for i in range(5):
            y = chart_y + int(chart_h * i / 4)
            val = max_val * (4 - i) / 4
            label = f"${val:.2f}" if val >= 0.01 else f"${val:.4f}"
            painter.drawText(
                0, y - 10, left_margin - 5, 20,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

        # 绘制柱子
        for i, (label, value) in enumerate(self.data.items()):
            x = start_x + i * (bar_w + bar_gap)
            bar_h = int((value / max_val) * chart_h) if max_val > 0 else 0
            y = chart_y + chart_h - bar_h

            # 柱子
            color = QColor(colors[i % len(colors)])
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)

            # 柱顶数值
            painter.setPen(QColor(get_label_color(theme)))
            painter.setFont(QFont("Microsoft YaHei", 9))
            val_text = f"${value:.2f}" if value >= 0.01 else f"${value:.4f}"
            painter.drawText(
                x - 10, y - 20, bar_w + 20, 20,
                Qt.AlignmentFlag.AlignCenter, val_text,
            )

            # X轴标签
            painter.setPen(text_color)
            display_label = label[:10] + '..' if len(label) > 10 else label
            painter.drawText(
                x - 10, chart_y + chart_h + 5, bar_w + 20, 25,
                Qt.AlignmentFlag.AlignCenter, display_label,
            )

        painter.end()


# ============ 统计卡片 ============

class StatCard(QWidget):
    """统计卡片"""

    def __init__(self, title: str, value: str, color: str = "#4A90D9", parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self._color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {get_label_color(secondary=True)}; font-size: 12px;"
        )
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(self.value_label)

        self.setStyleSheet(get_card_stylesheet())

    def update_value(self, value: str) -> None:
        self.value_label.setText(value)

    def apply_theme(self) -> None:
        """应用当前主题"""
        self.setStyleSheet(get_card_stylesheet())
        self.title_label.setStyleSheet(
            f"color: {get_label_color(secondary=True)}; font-size: 12px;"
        )


# ============ 成本统计主界面 ============

class CostWidget(QWidget):
    """成本统计界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_stats()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        header = QLabel("成本统计")
        header.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {get_label_color()};"
        )
        layout.addWidget(header)

        # 统计卡片行
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.total_cost_card = StatCard("总花费", "$0.00", "#E74C3C")
        self.month_cost_card = StatCard("本月花费", "$0.00", "#F39C12")
        self.total_tokens_card = StatCard("总Tokens", "0", "#3498DB")
        self.record_count_card = StatCard("调用次数", "0", "#2ECC71")

        cards_layout.addWidget(self.total_cost_card)
        cards_layout.addWidget(self.month_cost_card)
        cards_layout.addWidget(self.total_tokens_card)
        cards_layout.addWidget(self.record_count_card)

        layout.addLayout(cards_layout)

        # 图表区域
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)

        self.provider_chart = BarChartWidget(title="按提供商花费")
        self.model_chart = BarChartWidget(title="按模型花费")

        charts_layout.addWidget(self.provider_chart)
        charts_layout.addWidget(self.model_chart)

        layout.addLayout(charts_layout)

        # 筛选区域
        filter_group = QGroupBox("筛选")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("时间范围:"))
        self.range_combo = QComboBox()
        self.range_combo.addItems(
            ["全部", "最近7天", "最近30天", "最近90天", "自定义"]
        )
        self.range_combo.currentTextChanged.connect(self._on_range_changed)
        filter_layout.addWidget(self.range_combo)

        filter_layout.addWidget(QLabel("从:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.now() - timedelta(days=30))
        self.start_date.setEnabled(False)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("到:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.now())
        self.end_date.setEnabled(False)
        filter_layout.addWidget(self.end_date)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(get_primary_button_stylesheet())
        refresh_btn.clicked.connect(self._load_stats)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # 按提供商统计表
        provider_group = QGroupBox("按提供商统计")
        provider_layout = QVBoxLayout(provider_group)
        self.provider_table = QTableWidget()
        self.provider_table.setColumnCount(3)
        self.provider_table.setHorizontalHeaderLabels(["提供商", "花费", "占比"])
        self.provider_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.provider_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.provider_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        provider_layout.addWidget(self.provider_table)
        layout.addWidget(provider_group)

        # 按模型统计表
        model_group = QGroupBox("按模型统计")
        model_layout = QVBoxLayout(model_group)
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(3)
        self.model_table.setHorizontalHeaderLabels(["模型", "花费", "占比"])
        self.model_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.model_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.model_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        model_layout.addWidget(self.model_table)
        layout.addWidget(model_group)

        # 优化建议
        tips_group = QGroupBox("成本优化建议")
        tips_layout = QVBoxLayout(tips_group)
        self.tips_label = QLabel("加载中...")
        self.tips_label.setWordWrap(True)
        self.tips_label.setStyleSheet(f"padding: 8px; color: {get_label_color(secondary=True)};")
        tips_layout.addWidget(self.tips_label)
        layout.addWidget(tips_group)

        layout.addStretch()

    def _on_range_changed(self, text: str):
        is_custom = text == "自定义"
        self.start_date.setEnabled(is_custom)
        self.end_date.setEnabled(is_custom)

    def _get_date_range(self):
        range_text = self.range_combo.currentText()
        now = datetime.now()

        if range_text == "全部":
            return None, None
        elif range_text == "最近7天":
            return (now - timedelta(days=7)).strftime("%Y-%m-%d"), now.strftime(
                "%Y-%m-%d"
            )
        elif range_text == "最近30天":
            return (now - timedelta(days=30)).strftime("%Y-%m-%d"), now.strftime(
                "%Y-%m-%d"
            )
        elif range_text == "最近90天":
            return (now - timedelta(days=90)).strftime("%Y-%m-%d"), now.strftime(
                "%Y-%m-%d"
            )
        else:  # 自定义
            return (
                self.start_date.date().toString("yyyy-MM-dd"),
                self.end_date.date().toString("yyyy-MM-dd"),
            )

    def _load_stats(self):
        start_date, end_date = self._get_date_range()
        stats = cost_tracker.get_stats(start_date, end_date)

        # 更新卡片
        self.total_cost_card.update_value(f"${stats['total_cost']:.4f}")
        self.total_tokens_card.update_value(f"{stats['total_tokens']:,}")
        self.record_count_card.update_value(f"{stats['record_count']:,}")

        # 本月花费
        monthly = cost_tracker.get_monthly_summary()
        self.month_cost_card.update_value(f"${monthly['total_cost']:.4f}")

        # 更新图表
        self.provider_chart.update_data(stats['by_provider'])
        self.model_chart.update_data(stats['by_model'])

        # 提供商表格
        self.provider_table.setRowCount(len(stats['by_provider']))
        for i, (provider, cost) in enumerate(
            sorted(stats['by_provider'].items(), key=lambda x: x[1], reverse=True)
        ):
            self.provider_table.setItem(i, 0, QTableWidgetItem(provider))
            self.provider_table.setItem(i, 1, QTableWidgetItem(f"${cost:.4f}"))
            pct = (cost / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
            self.provider_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))

        # 模型表格
        self.model_table.setRowCount(len(stats['by_model']))
        for i, (model, cost) in enumerate(
            sorted(stats['by_model'].items(), key=lambda x: x[1], reverse=True)
        ):
            self.model_table.setItem(i, 0, QTableWidgetItem(model))
            self.model_table.setItem(i, 1, QTableWidgetItem(f"${cost:.4f}"))
            pct = (cost / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
            self.model_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))

        # 优化建议
        tips = cost_tracker.get_optimization_tips()
        self.tips_label.setText("\n".join(f"  {t}" for t in tips))

    def apply_theme(self) -> None:
        """应用当前主题"""
        for card in [
            self.total_cost_card,
            self.month_cost_card,
            self.total_tokens_card,
            self.record_count_card,
        ]:
            card.apply_theme()
