"""
统计管理器 — 负责抽取统计数据的 CRUD、概率计算、导出。
"""
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from config import Config


class StatisticsManager:
    """抽取统计管理器 — 数据 CRUD + 概率计算"""

    def __init__(self):
        self.stats: dict = {}
        self._probabilities_cache: dict | None = None

    # ── 持久化 ──

    def load_from_json(self):
        self.stats = Config.read_json(Config.get_stats_file(), {})

    def save_to_json(self):
        Config.write_json(Config.get_stats_file(), self.stats)

    # ── 概率计算 ──

    def calculate_probabilities(self, students: list) -> dict:
        """逆频次加权：被抽中越少概率越高。结果缓存于 _probabilities_cache。"""
        if self._probabilities_cache is None:
            probs = {
                s: 1 / (len(students) * (self.stats.get(s, 0) + 1))
                for s in students
            }
            total = sum(probs.values())
            if total > 0:
                probs = {k: v / total for k, v in probs.items()}
            self._probabilities_cache = probs
        return self._probabilities_cache

    def invalidate_cache(self):
        self._probabilities_cache = None

    # ── 键同步 ──

    def ensure_initialized(self, students: list):
        """同步 stats 键与 students 集合（新增/删除的条目）"""
        student_set = set(students)
        stat_keys = set(self.stats.keys())
        for s in student_set - stat_keys:
            self.stats[s] = 0
        for s in stat_keys - student_set:
            del self.stats[s]
        if student_set != stat_keys:
            self.invalidate_cache()  # P0-1: 键集变更后必须失效概率缓存
            self.save_to_json()

    # ── 用户操作 ──

    def increment(self, name: str):
        """增加某一学生的抽取次数，自动保存并失效概率缓存 (P1-1)"""
        self.stats[name] = self.stats.get(name, 0) + 1
        self.save_to_json()
        self.invalidate_cache()

    def reset(self, parent=None) -> bool:
        """确认后重置统计数据。返回是否已重置。"""
        if parent is not None:
            reply = QMessageBox.question(
                parent, "确认重置",
                "是否确认重置所有统计数据？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False
        self.stats = {}
        self.invalidate_cache()
        return True

    def export_json(self, parent=None):
        """导出统计数据到 JSON 文件"""
        path, _ = QFileDialog.getSaveFileName(
            parent, "导出统计数据", "statistics.json", "JSON Files (*.json)"
        )
        if path:
            return Config.write_json(path, self.stats)
        return False
