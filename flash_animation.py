"""
QTimer 动画 — 基于 QTimer 的名字闪动动画（替代 QThread）。
"""
import random
from PyQt5.QtCore import QTimer
from config import Config


class FlashAnimation:
    """基于 QTimer 的名字闪动动画"""
    def __init__(self, students, on_name, on_finish, on_tick=None):
        self.students = students
        self._snapshot = []  # start() 时冻结名单快照
        self._step = 0
        self._on_name = on_name
        self._on_finish = on_finish
        self._on_tick = on_tick
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._step = 0
        self._snapshot = list(self.students)  # 冻结快照，防止外部修改 students 导致崩溃
        self._timer.start(Config.ANIMATION_DELAY)

    def _tick(self):
        if self._step >= Config.ANIMATION_STEPS:
            self._timer.stop()
            self._on_finish()
            return
        self._on_name(random.choice(self._snapshot))
        if self._on_tick:
            self._on_tick()
        self._step += 1

    def stop(self):
        self._timer.stop()
