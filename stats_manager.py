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
        """三层公平性保护的概率计算 (P1-3)。

        步 1: 基础逆频次权重  w = 1/(N×(count+1))
        步 2: 平均值过滤 — 当 max-min > GAP_THRESHOLD 时，
               排除 count > 平均值的候选者
        步 3: 候选池下限保障 — 若候选池 < N×CANDIDATE_POOL_MIN_RATIO，
               按 count 升序补回足够学生
        结果缓存于 _probabilities_cache。
        """
        if self._probabilities_cache is not None:
            return self._probabilities_cache

        N = len(students)
        if N == 0:
            self._probabilities_cache = {}
            return self._probabilities_cache

        counts = {s: self.stats.get(s, 0) for s in students}
        max_count = max(counts.values())
        min_count = min(counts.values())
        mean_count = sum(counts.values()) / N

        # 步 1: 基础逆频次权重
        raw_weights = {s: 1.0 / (N * (counts[s] + 1)) for s in students}

        # 步 2: 平均值过滤（差距超阈值时触发）
        if max_count - min_count > Config.GAP_THRESHOLD:
            candidates = [s for s in students if counts[s] <= mean_count]
            # 步 3: 候选池下限保障
            min_pool = max(2, int(N * Config.CANDIDATE_POOL_MIN_RATIO))
            if len(candidates) < min_pool:
                excluded = sorted(
                    [s for s in students if counts[s] > mean_count],
                    key=lambda s: counts[s]
                )
                needed = min_pool - len(candidates)
                candidates.extend(excluded[:needed])
        else:
            candidates = list(students)

        # 步 4: 归一化候选池概率
        probs = {}
        total_weight = sum(raw_weights[s] for s in candidates)
        if total_weight > 0:
            for s in candidates:
                probs[s] = raw_weights[s] / total_weight
        # 非候选学生概率为 0
        for s in students:
            if s not in probs:
                probs[s] = 0.0

        self._probabilities_cache = probs
        return self._probabilities_cache

    def get_probability(self, student: str, students: list) -> float:
        """获取某个学生的当前被抽中概率（0.0–1.0），不触发缓存重建 (P1-3)"""
        if self._probabilities_cache is not None:
            return self._probabilities_cache.get(student, 0.0)
        self.calculate_probabilities(students)
        return self._probabilities_cache.get(student, 0.0)

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

    def increment_and_update_cache(self, name: str, students: list):
        """抽取后增量更新：计数 +1 → 立即重算概率缓存 (P1-3)"""
        self.stats[name] = self.stats.get(name, 0) + 1
        self.save_to_json()
        self.invalidate_cache()
        self.calculate_probabilities(students)  # 缓存预热

    def increment_batch_and_update_cache(self, names: list, students: list):
        """多人抽取后批量更新：所有学生计数 +1 → 立即重算概率缓存 (P1-3)"""
        for name in names:
            self.stats[name] = self.stats.get(name, 0) + 1
        self.save_to_json()
        self.invalidate_cache()
        self.calculate_probabilities(students)  # 缓存预热

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
