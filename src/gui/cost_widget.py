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


class StatCard(QWidget):
    """统计卡片"""

    def __init__(self, title: str, value: str, color: str = "#4A90D9", parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)

        self.setStyleSheet(
            "StatCard { background: white; border-radius: 8px; border: 1px solid #E0E0E0; }"
        )

    def update_value(self, value: str):
        self.value_label.setText(value)


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
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
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

        # 筛选区域
        filter_group = QGroupBox("筛选")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("时间范围:"))
        self.range_combo = QComboBox()
        self.range_combo.addItems(["全部", "最近7天", "最近30天", "最近90天", "自定义"])
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
        refresh_btn.setStyleSheet(
            "QPushButton { background-color: #4A90D9; color: white; border: none; border-radius: 4px; padding: 6px 16px; }"
            "QPushButton:hover { background-color: #357ABD; }"
        )
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
        self.provider_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.provider_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.provider_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        provider_layout.addWidget(self.provider_table)
        layout.addWidget(provider_group)

        # 按模型统计表
        model_group = QGroupBox("按模型统计")
        model_layout = QVBoxLayout(model_group)
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(3)
        self.model_table.setHorizontalHeaderLabels(["模型", "花费", "占比"])
        self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.model_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        model_layout.addWidget(self.model_table)
        layout.addWidget(model_group)

        # 优化建议
        tips_group = QGroupBox("成本优化建议")
        tips_layout = QVBoxLayout(tips_group)
        self.tips_label = QLabel("加载中...")
        self.tips_label.setWordWrap(True)
        self.tips_label.setStyleSheet("padding: 8px; color: #555;")
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
            return (now - timedelta(days=7)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        elif range_text == "最近30天":
            return (now - timedelta(days=30)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        elif range_text == "最近90天":
            return (now - timedelta(days=90)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        else:  # 自定义
            return self.start_date.date().toString("yyyy-MM-dd"), self.end_date.date().toString("yyyy-MM-dd")

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
