"""GUI入口文件"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from .. import __version__


def run_gui():
    """启动GUI应用"""
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AI Assistant")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("守诚知")

    # 设置默认字体
    from PyQt6.QtGui import QFont
    font = QFont("Microsoft YaHei", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    from .main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
