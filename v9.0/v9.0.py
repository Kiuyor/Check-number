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
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from config import Config
from splash_screen import SplashScreen
from main_window import RandomSelectorWindow

# ===== 高 DPI 适配（必须在 QApplication 构造之前） =====
# P3-5: AA_EnableHighDpiScaling / AA_UseHighDpiPixmaps 自 Qt 5.14 起弃用
# 仅在旧版 Qt 上启用 (Qt < 5.14)
try:
    from PyQt5.QtCore import QT_VERSION_STR
    _qt_major, _qt_minor, *_ = map(int, QT_VERSION_STR.split("."))
    if (_qt_major, _qt_minor) < (5, 14):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except Exception:
    # 无法检测版本时保留原行为（保守策略）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

try:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
except AttributeError:
    pass  # Qt < 5.14 无此 API
# =======================================================

def main():
    """应用入口 — Nuitka standalone 模式可编译此函数为原生代码"""
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
