"""
可拖动的圆形悬浮球 — 点击恢复窗口，拖拽移动位置 (P1-8: 从 main_window 提取)

注意：不使用 QGraphicsDropShadowEffect，因为小尺寸 (40x40) + WA_TranslucentBackground
在 Windows 上会导致 UpdateLayeredWindowIndirect 失败（阴影脏区域超出边界）。
"""
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPoint
from config import Config
from design_tokens import DesignTokens


class FloatBall(QPushButton):
    """可拖动的圆形悬浮球 — 点击恢复窗口，拖拽移动位置"""

    def __init__(self):
        super().__init__(None)
        self.setObjectName("floatBtn")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(Config.FLOAT_SIZE, Config.FLOAT_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_ball_style()

        self._restore_callback = None
        self._drag_active = False
        self._press_global = QPoint()

    def _apply_ball_style(self):
        """应用当前主题的悬浮球颜色 (P2-7: 使用 DesignTokens ball_bg/ball_hover)"""
        t = DesignTokens.get(Config.color_scheme)
        self.setStyleSheet(
            f"QPushButton {{ background: {t['ball_bg']}; border: none; border-radius: 20px; }}"
            f"QPushButton:hover {{ background: {t['ball_hover']}; }}"
        )

    def refresh_theme(self):
        """主题切换后刷新悬浮球样式"""
        self._apply_ball_style()

    def set_restore_callback(self, callback):
        """设置点击回调（无拖动时触发）"""
        self._restore_callback = callback

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._press_global = event.globalPos()
            self._press_origin = self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton:
            delta = event.globalPos() - self._press_global
            self.move(self._press_origin + delta)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_active:
            self._drag_active = False
            delta = event.globalPos() - self._press_global
            # 移动距离 < 5px 视为点击 → 恢复窗口
            if delta.manhattanLength() < 5 and self._restore_callback:
                self._restore_callback()
        super().mouseReleaseEvent(event)
