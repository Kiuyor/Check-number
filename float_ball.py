"""
可拖动的圆形悬浮球 — 点击恢复窗口，拖拽移动位置

白色半透明设计，透明度可通过 Config.ball_opacity 调节。

注意：不使用 QGraphicsDropShadowEffect，因为小尺寸 (40x40) + WA_TranslucentBackground
在 Windows 上会导致 UpdateLayeredWindowIndirect 失败（阴影脏区域超出边界）。
"""
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QPoint
from config import Config


class FloatBall(QPushButton):
    """白色可调透明度悬浮球 — 点击恢复窗口，拖拽移动位置"""

    _ALPHA = 255          # 颜色通道 alpha（0–255），用于 hover 微调
    _CLICK_THRESHOLD = 5  # 拖/点区分阈值 (px)，移动 < 此值视为点击（P2-5）

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
        self._press_origin = QPoint()

    def _apply_ball_style(self):
        """应用白色 + 可调透明度样式"""
        alpha = int(Config.ball_opacity * self._ALPHA)
        hover_alpha = int(min(1.0, Config.ball_opacity + 0.12) * self._ALPHA)
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background: rgba(255, 255, 255, {alpha});"
            f"  border: 1px solid rgba(180, 180, 180, {alpha});"
            f"  border-radius: 20px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: rgba(245, 245, 245, {hover_alpha});"
            f"  border: 1px solid rgba(160, 160, 160, {hover_alpha});"
            f"}}"
        )

    def refresh_theme(self):
        """主题切换时刷新（球体白色不变，但 Config 可能更新）"""
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
            if delta.manhattanLength() < self._CLICK_THRESHOLD and self._restore_callback:
                self._restore_callback()
        super().mouseReleaseEvent(event)
