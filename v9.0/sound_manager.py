"""
音效管理 — 基于 winsound.Beep + QTimer 非阻塞调度。
"""
from PyQt5.QtCore import QTimer

# P0-6: 将 winsound 导入提升至模块级别，避免热路径中的重复 import 开销
try:
    import winsound
    _HAS_WINSOUND = True
except Exception:
    _HAS_WINSOUND = False


class SoundManager:
    """音效管理 — winsound.Beep 合成音效，QTimer 串联非阻塞调度"""

    @staticmethod
    def _beep(freq: int, duration_ms: int):
        """单次蜂鸣（win32 专有，其他平台静默降级）"""
        if _HAS_WINSOUND:
            try:
                winsound.Beep(freq, duration_ms)
            except Exception:
                pass

    @staticmethod
    def play_flash_tick():
        """闪动过程中的短促点击音"""
        SoundManager._beep(1200, 15)

    @staticmethod
    def play_start():
        """抽取开始 — 两个上升音 (A4→E5)"""
        SoundManager._beep(440, 80)
        QTimer.singleShot(100, lambda: SoundManager._beep(660, 80))

    @staticmethod
    def play_result():
        """结果揭晓 — 三音下行 (A5→E5→A4)"""
        SoundManager._beep(880, 80)
        QTimer.singleShot(100, lambda: SoundManager._beep(660, 80))
        QTimer.singleShot(200, lambda: SoundManager._beep(440, 160))
