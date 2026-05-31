"""
抽取历史管理器 — 负责历史记录的 CRUD 和持久化。
"""
import json
import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from config import Config


class HistoryManager:
    """抽取历史记录管理器"""

    def __init__(self):
        self.history: list = []

    # ── JSON 工具 ──

    @staticmethod
    def _read_json(file_path: str, default=None):
        """读取 JSON 文件，带错误分类处理"""
        if default is None:
            default = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default
        except json.JSONDecodeError as e:
            print(f"[History] JSON 文件损坏 ({file_path}): {e}", file=sys.stderr)
            try:
                os.rename(file_path, file_path + ".corrupted")
                print(f"[History] 已备份损坏文件 → {file_path}.corrupted", file=sys.stderr)
            except OSError:
                pass
            return default
        except (PermissionError, OSError) as e:
            print(f"[History] 文件读取失败 ({file_path}): {e}", file=sys.stderr)
            return default

    @staticmethod
    def _write_json(file_path: str, data) -> bool:
        """写入 JSON 文件，带错误处理"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (PermissionError, OSError) as e:
            print(f"[History] 文件写入失败 ({file_path}): {e}", file=sys.stderr)
            return False

    # ── 持久化 ──

    def load_from_json(self) -> list:
        """从配置文件加载历史记录"""
        self.history = self._read_json(Config.get_history_file(), [])
        return self.history

    def save_to_json(self):
        """保存历史记录（自动截断）"""
        if len(self.history) > Config.MAX_HISTORY_RECORDS:
            self.history = self.history[-Config.MAX_HISTORY_RECORDS:]
        self._write_json(Config.get_history_file(), self.history)

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
