"""
音效管理 — 基于 winsound.Beep + QTimer 非阻塞调度。
"""
from PyQt5.QtCore import QTimer

# P0-6: 将 winsound 导入提升至模块级别，避免热路径中的重复 import 开销
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False


class SoundManager:
    """音效管理 — winsound.Beep 合成音效，QTimer 串联非阻塞调度"""

    # 音符频率 (Hz)
    NOTE_A4 = 440
    NOTE_E5 = 660
    NOTE_A5 = 880
    NOTE_FLASH_TICK = 1200

    # 时长 (ms)
    TICK_MS = 15
    NOTE_MS = 80
    END_NOTE_MS = 160
    BEAT_MS = 100  # 音符间隔

    @staticmethod
    def _beep(freq: int, duration_ms: int):
        """单次蜂鸣（win32 专有，其他平台静默降级）"""
        if _HAS_WINSOUND:
            try:
                winsound.Beep(freq, duration_ms)
            except (RuntimeError, OSError):
                pass

    @staticmethod
    def play_flash_tick():
        """闪动过程中的短促点击音"""
        SoundManager._beep(SoundManager.NOTE_FLASH_TICK, SoundManager.TICK_MS)

    @staticmethod
    def play_start():
        """抽取开始 — 两个上升音 (A4→E5)"""
        SoundManager._beep(SoundManager.NOTE_A4, SoundManager.NOTE_MS)
        QTimer.singleShot(SoundManager.BEAT_MS,
                          lambda: SoundManager._beep(SoundManager.NOTE_E5, SoundManager.NOTE_MS))

    @staticmethod
    def play_result():
        """结果揭晓 — 三音下行 (A5→E5→A4)"""
        SoundManager._beep(SoundManager.NOTE_A5, SoundManager.NOTE_MS)
        QTimer.singleShot(SoundManager.BEAT_MS,
                          lambda: SoundManager._beep(SoundManager.NOTE_E5, SoundManager.NOTE_MS))
        QTimer.singleShot(SoundManager.BEAT_MS * 2,
                          lambda: SoundManager._beep(SoundManager.NOTE_A4, SoundManager.END_NOTE_MS))
