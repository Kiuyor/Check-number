"""
随机点名器 v9.0 — Impeccable 设计方法论 × PyQt5
基于加权概率的随机抽取工具，根据历史抽取次数动态调整概率。

模块结构：
  design_tokens.py  — 配色方案（6 套）
  config.py         — 配置、路径、偏好、QSS
  flash_animation.py— 名字闪动动画
  sound_manager.py  — winsound 音效
  splash_screen.py  — 启动画面
  float_ball.py     — 可拖拽悬浮球
  main_window.py    — 主窗口（UI + 业务逻辑）
"""
import sys
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from config import Config
from splash_screen import SplashScreen
from main_window import RandomSelectorWindow


def _setup_dpi():
    """高 DPI 适配（必须在 QApplication 构造之前调用）

    Windows 下 125%/150%/175% 缩放显示的核心适配。

    机制说明：
      1. Nuitka 编译时需加 --windows-dpi-awareness=per-monitor-v2
         让 exe 向 Windows 声明"我能自己处理 DPI"，避免位图拉伸模糊
      2. PassThrough 舍入策略支持 125%/150%/175% 等非整数倍缩放
    """
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        pass  # Qt < 5.14 无此 API


def main():
    """应用入口 — Nuitka standalone 模式可编译此函数为原生代码"""
    _setup_dpi()
    app = QApplication(sys.argv)

    # 全局字体
    app.setFont(Config.get_font(11))

    # 必须在创建窗口前加载偏好，确保 SplashScreen 使用正确的配色
    Config.load_preferences()

    # 启动画面
    splash = SplashScreen(scheme_key=Config.color_scheme)
    splash.show()
    app.processEvents()

    # 主窗口
    window = RandomSelectorWindow()
    window.show()

    # Splash 淡出 → 主窗口获得焦点
    splash.fade_out(window)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
