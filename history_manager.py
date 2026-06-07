"""
抽取历史管理器 — 负责历史记录的 CRUD 和持久化。
"""
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from config import Config


class HistoryManager:
    """抽取历史记录管理器"""

    def __init__(self):
        self.history: list = []

    # ── 持久化 ──

    def load_from_json(self) -> list:
        """从配置文件加载历史记录"""
        self.history = Config.read_json(Config.get_history_file(), [])
        return self.history

    def save_to_json(self):
        """保存历史记录（自动截断）"""
        if len(self.history) > Config.MAX_HISTORY_RECORDS:
            self.history = self.history[-Config.MAX_HISTORY_RECORDS:]
        Config.write_json(Config.get_history_file(), self.history)

    # ── 记录管理 ──

    def add_record(self, results: list):
        """添加一条抽取历史记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "mode": "multi" if len(results) > 1 else "single",
            "results": results,
        }
        self.history.append(record)
        self.save_to_json()

    def clear(self, parent=None) -> bool:
        """确认后清空所有历史记录。返回是否已清空。"""
        if parent is not None:
            reply = QMessageBox.question(
                parent, "确认清除",
                "是否清除所有抽取历史记录？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False
        self.history = []
        self.save_to_json()
        return True

    def clear_from_dialog(self, dialog):
        """从对话框内部清空历史并关闭对话框"""
        self.history = []
        self.save_to_json()
        dialog.accept()
