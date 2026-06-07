"""
启动画面 — 圆角半透明窗口，显示应用名后淡出。
"""
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from design_tokens import DesignTokens
from config import Config


class SplashScreen(QWidget):
    """启动动画 — 圆角半透明窗口，显示应用名后淡出"""

    # P3-2: 将点动画帧提升为类级常量，避免每 400ms 重新分配列表
    _DOT_FRAMES = ["· · ·", "• · ·", "· • ·", "· · •"]
    _WINDOW_SIZE = (240, 140)
    _TITLE_Y = 28
    _SUBTITLE_Y = 70
    _DOTS_Y = 100

    def __init__(self, scheme_key: str = "indigo"):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        w, h = self._WINDOW_SIZE
        self.setFixedSize(w, h)

        t = DesignTokens.get(scheme_key)

        # 背景圆角卡片
        self._bg = QFrame(self)
        self._bg.setGeometry(0, 0, *self._WINDOW_SIZE)
        self._bg.setStyleSheet(f"""
            QFrame {{
                background-color: {t['surface_solid']};
                border-radius: 16px;
                border: 2px solid {t['border']};
            }}
        """)

        # 标题
        title = QLabel("Check Number", self._bg)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(Config.get_font(22, bold=True))
        title.setStyleSheet(f"color: {t['splash_title_fg']}; background: transparent;")
        title.setGeometry(0, self._TITLE_Y, w, 40)

        # 副标题
        subtitle = QLabel("随机点名器", self._bg)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(Config.get_font(12))
        subtitle.setStyleSheet(f"color: {t['splash_subtitle_fg']}; background: transparent;")
        subtitle.setGeometry(0, self._SUBTITLE_Y, w, 24)

        # 进度指示器（三个点）
        self._dots = QLabel("· · ·", self._bg)
        self._dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots.setFont(Config.get_font(16))
        self._dots.setStyleSheet(f"color: {t['splash_dots_fg']}; background: transparent;")
        self._dots.setGeometry(0, self._DOTS_Y, w, 24)
        self._dot_timer = QTimer()
        self._dot_frame = 0
        self._dot_timer.timeout.connect(self._animate_dots)
        self._dot_timer.start(400)

        # 屏幕居中
        self._center_on_screen()

        # 淡入
        self._fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fade_effect)
        self._fade_in = QPropertyAnimation(self._fade_effect, b"opacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_in.start()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            w, h = self._WINDOW_SIZE
            self.move((geo.width() - w) // 2, (geo.height() - h) // 2)

    def _animate_dots(self):
        self._dot_frame = (self._dot_frame + 1) % len(self._DOT_FRAMES)
        self._dots.setText(self._DOT_FRAMES[self._dot_frame])

    def fade_out(self, target_window):
        """淡出后关闭，然后激活主窗口 (P1-9: 显式链式调用，消除信号时序依赖)"""
        self._dot_timer.stop()
        self._fade_out = QPropertyAnimation(self._fade_effect, b"opacity")
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.InCubic)

        def _on_finished():
            self.close()
            # 延迟到下一事件循环，确保 close() 完成后再激活主窗口
            QTimer.singleShot(0, lambda: (
                target_window.raise_(),
                target_window.activateWindow()
            ))

        self._fade_out.finished.connect(_on_finished)
        self._fade_out.start()
