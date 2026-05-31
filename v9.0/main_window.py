"""
随机点名器 v9.0 — 主窗口
基于加权概率的随机抽取工具，根据历史抽取次数动态调整概率。
"""
import random
import os
import sys
import io
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMenu, QMessageBox, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QGraphicsOpacityEffect,
    QShortcut, QAbstractItemView,
)
from PyQt5.QtCore import (
    QTimer, QPropertyAnimation, Qt, QEasingCurve, QPoint,
)
from PyQt5.QtGui import QFont, QColor, QKeySequence
from design_tokens import DesignTokens
from config import Config
from flash_animation import FlashAnimation
from sound_manager import SoundManager
from float_ball import FloatBall  # P1-8


class RandomSelectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ── 状态 ──
        self._drag_active = False
        self._drag_position = None
        self.students: list = []
        self.stats: dict = {}
        self._toast = None
        self._toast_animation = None
        self._probabilities_cache = None
        self._flash = None
        self._result_animation = None  # 保持引用防止被 GC

        # ── 功能状态 ──
        self.sound_enabled = Config.sound_enabled
        self.draw_history: list = []
        self.fast_mode_enabled = False

        # ── 初始化 ──
        self.setup_ui()
        self.setup_window_properties()
        self._apply_theme()
        self.setup_shortcuts()

        # 延迟 I/O，让窗口先显示
        QTimer.singleShot(0, self._deferred_init)

    # ═══════════════════════════════════════════════════════════════
    # JSON 文件读写工具 (P1-3: 消除 4 处重复)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _read_json(file_path: str, default=None):
        """读取 JSON 文件，带错误分类处理 (P0-3)"""
        if default is None:
            default = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default
        except json.JSONDecodeError as e:
            print(f"[MainWindow] JSON 文件损坏 ({file_path}): {e}", file=sys.stderr)
            # 备份损坏文件
            try:
                os.rename(file_path, file_path + ".corrupted")
                print(f"[MainWindow] 已备份损坏文件 → {file_path}.corrupted", file=sys.stderr)
            except OSError:
                pass
            return default
        except (PermissionError, OSError) as e:
            print(f"[MainWindow] 文件读取失败 ({file_path}): {e}", file=sys.stderr)
            return default

    @staticmethod
    def _write_json(file_path: str, data):
        """写入 JSON 文件，带错误处理 (P0-3)"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (PermissionError, OSError) as e:
            print(f"[MainWindow] 文件写入失败 ({file_path}): {e}", file=sys.stderr)
            return False

    # ═══════════════════════════════════════════════════════════════
    # 延迟初始化
    # ═══════════════════════════════════════════════════════════════

    def _deferred_init(self):
        """窗口显示后加载数据"""
        self._load_stats()
        self.draw_history = self._load_history()
        self.prepare_students_file()
        self.ensure_statistics_initialized()

    # ═══════════════════════════════════════════════════════════════
    # 主题管理
    # ═══════════════════════════════════════════════════════════════

    def _apply_theme(self):
        """应用全局样式并刷新组件级颜色 (P2-4)"""
        QApplication.instance().setStyleSheet(Config.get_stylesheet())
        self._update_shadow_style()
        self._refresh_widget_colors()

    def _refresh_widget_colors(self):
        """刷新内联样式颜色以跟随主题切换 (P2-4)"""
        t = DesignTokens.get(Config.color_scheme)
        # 结果标签初始颜色
        self.result_label.setStyleSheet(
            f"color: {t['text_primary']}; background: transparent;"
        )
        # 状态标签
        self.status_label.setStyleSheet(
            f"color: {t['text_secondary']}; background: transparent;"
        )
        # 悬浮球主题
        if hasattr(self, 'float_window') and self.float_window is not None:
            self.float_window.refresh_theme()

    def _apply_color_scheme(self, key: str):
        """切换配色方案 (P1-2: 使用 Config.set_color_scheme)"""
        Config.set_color_scheme(key)
        self._apply_theme()
        name = DesignTokens.get_scheme_name(key)
        self.show_toast(f"配色：{name}")

    def _cycle_color_scheme(self):
        """循环切换配色方案"""
        schemes = DesignTokens.list_schemes()
        current = Config.color_scheme
        keys = [k for k, _ in schemes]
        try:
            idx = keys.index(current)
            next_key = keys[(idx + 1) % len(keys)]
        except ValueError:
            next_key = keys[0]
        self._apply_color_scheme(next_key)

    # ═══════════════════════════════════════════════════════════════
    # 快捷键
    # ═══════════════════════════════════════════════════════════════

    def setup_shortcuts(self):
        """注册键盘快捷键 (P1-7: 使用 minimize_to_float)"""
        QShortcut(QKeySequence("Space"), self).activated.connect(self.start_draw_process)
        QShortcut(QKeySequence("Return"), self).activated.connect(self.start_draw_process)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.minimize_to_float)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self._cycle_color_scheme)

    # ═══════════════════════════════════════════════════════════════
    # 数据持久化
    # ═══════════════════════════════════════════════════════════════

    def _load_stats(self):
        self.stats = self._read_json(Config.get_stats_file(), {})

    def _save_stats(self):
        self._write_json(Config.get_stats_file(), self.stats)

    def _load_history(self):
        return self._read_json(Config.get_history_file(), [])

    def _save_history(self):
        """保存抽取历史记录（自动截断至 MAX_HISTORY_RECORDS）"""
        if len(self.draw_history) > Config.MAX_HISTORY_RECORDS:
            self.draw_history = self.draw_history[-Config.MAX_HISTORY_RECORDS:]
        self._write_json(Config.get_history_file(), self.draw_history)

    def _add_history_record(self, results: list):
        """添加一条抽取历史记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "mode": "multi" if len(results) > 1 else "single",
            "results": results,
        }
        self.draw_history.append(record)
        self._save_history()

    # ═══════════════════════════════════════════════════════════════
    # 名单管理 (P0-4: 内存解密; P0-5: 原子写入)
    # ═══════════════════════════════════════════════════════════════

    def prepare_students_file(self):
        """启动时准备学生名单"""
        base_dir = Config.get_base_dir()
        os.makedirs(base_dir, exist_ok=True)
        student_path = Config.get_student_file()
        enc_path = Config.get_enc_file()

        # 步 1: 若明文文件存在，加密后删除 (P0-5: 不覆盖已有 enc)
        if os.path.exists(student_path):
            if os.path.exists(enc_path):
                # 两份文件同时存在 → 不覆盖，仅删除明文（可能用户手动放置）
                try:
                    os.remove(student_path)
                    self.show_toast("检测到名单文件，已保留加密版本")
                except OSError:
                    self.show_toast("名单文件清理失败")
            else:
                try:
                    with open(student_path, "rb") as f:
                        content = f.read()
                    encrypted = self.xor_encrypt_decrypt(content, Config.PASSWORD)
                    # 原子写入：先写临时文件，再重命名 (P0-5)
                    tmp_path = enc_path + ".tmp"
                    with open(tmp_path, "wb") as f:
                        f.write(encrypted)
                    os.replace(tmp_path, enc_path)  # Win 上原子操作
                    os.remove(student_path)
                    self.show_toast("已加密名单并删除原文件")
                except OSError as e:
                    self.show_toast(f"名单加密失败: {e}")

        # 步 2: 加载加密名单
        if os.path.exists(enc_path):
            names = self._decrypt_in_memory(enc_path)
            if names is not None:
                self.load_students_from_list(names)
            else:
                self.students = [str(i) for i in range(1, Config.NUM_STUDENTS + 1)]
                self.show_toast("名单解密失败，已恢复默认")
        else:
            self.students = [str(i) for i in range(1, Config.NUM_STUDENTS + 1)]
            self.show_toast("未找到名单，已恢复默认")

    def load_students(self, file_path=None):
        """从文件加载学生名单"""
        if file_path is None:
            self.show_toast("未指定名单路径")
            return
        students = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name:
                        students.append(name)
        except Exception as e:
            self.show_toast(f"名单读取失败: {e}")
            return
        self.load_students_from_list(students)

    def load_students_from_list(self, students: list):
        """从列表加载学生名单"""
        if students:
            self.students = students
            self.ensure_statistics_initialized()
            self.show_toast(f"名单已加载（共{len(students)}人）")
        else:
            self.students = [str(i) for i in range(1, Config.NUM_STUDENTS + 1)]
            self.show_toast("名单为空，已恢复默认")

    def import_student_list(self):
        """通过文件对话框导入名单，加密保存并替换当前名单"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入学生名单",
            Config.get_base_dir(),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return

        # 读取文件
        students = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name:
                        students.append(name)
        except Exception as e:
            self.show_toast(f"名单读取失败: {e}")
            return

        if not students:
            self.show_toast("名单为空，未做更改")
            return

        # 加密保存到 names.enc（持久化：关闭后不重置）
        enc_path = Config.get_enc_file()
        try:
            content = '\n'.join(students).encode('utf-8')
            encrypted = self.xor_encrypt_decrypt(content, Config.PASSWORD)
            with open(enc_path, 'wb') as f:
                f.write(encrypted)
        except OSError as e:
            self.show_toast(f"名单保存失败: {e}")
            return

        # 替换当前名单并重置统计
        self.stats = {}
        self._probabilities_cache = None
        self.load_students_from_list(students)

    # ═══════════════════════════════════════════════════════════════
    # 加密工具
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def xor_encrypt_decrypt(data: bytes, key: str) -> bytes:
        """XOR 对称加解密 (P1-5: 改为 @staticmethod)"""
        key_bytes = key.encode('utf-8')
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

    def _decrypt_in_memory(self, enc_path: str):
        """解密 enc 文件，完全在内存中操作 (P0-4: 不再写临时文件)"""
        try:
            with open(enc_path, "rb") as f:
                encrypted = f.read()
            decrypted = self.xor_encrypt_decrypt(encrypted, Config.PASSWORD)
            text = decrypted.decode("utf-8")
            # 解析为名字列表
            names = [line.strip() for line in text.splitlines() if line.strip()]
            return names
        except Exception as e:
            self.show_toast(f"名单解密失败: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════════════════════════

    def setup_ui(self):
        t = DesignTokens.get(Config.color_scheme)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addStretch()

        # 结果标签
        self.result_label = QLabel("双击抽取", self)
        self.result_label.setObjectName("resultLabel")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(Config.get_font(Config.RESULT_FONT_SIZE, bold=True))
        self.result_label.setStyleSheet(
            f"color: {t['text_primary']}; background: transparent;"
        )
        self.main_layout.addWidget(self.result_label)

        self.main_layout.addStretch()

        # 状态标签（绝对定位在底部）
        self.status_label = QLabel("", self.central_widget)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(Config.get_font(11))
        self.status_label.setStyleSheet(
            f"color: {t['text_secondary']}; background: transparent;"
        )
        self.status_label.setFixedHeight(Config.STATUS_LABEL_HEIGHT)

        # macOS 风格 — 左上角红色最小化按钮
        mx, my = Config.MIN_BTN_POS
        self.min_btn = QPushButton("", self.central_widget)
        self.min_btn.setObjectName("macCloseBtn")
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setToolTip("最小化")
        self.min_btn.clicked.connect(self.minimize_to_float)
        self.min_btn.move(mx, my)

        # macOS 风格 — 右下角快速模式按钮
        self.fast_btn = QPushButton("", self.central_widget)
        self.fast_btn.setObjectName("macFastBtn")
        self.fast_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fast_btn.setToolTip("快速模式 — 关闭")
        self.fast_btn.clicked.connect(self._toggle_fast_mode)

        # 延迟定位右下角按钮
        QTimer.singleShot(0, self._position_overlays)

        # 悬浮球
        self.float_window = FloatBall()
        self.float_window.set_restore_callback(self.restore_from_float)
        self.float_window.hide()

    def setup_window_properties(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen()
        width, height = Config.WINDOW_SIZE
        if screen:
            geometry = screen.geometry()
            x = Config.window_x if Config.window_x is not None else (geometry.width() - width) // 2
            y = Config.window_y if Config.window_y is not None else (geometry.height() - height) // 2
            x = max(0, min(x, geometry.width() - 40))
            y = max(0, min(y, geometry.height() - 40))
            self.setGeometry(x, y, width, height)
            self.setFixedSize(width, height)
        self.shadow = QFrame(self.central_widget)
        self.shadow.setGeometry(0, 0, width, height)
        self._update_shadow_style()
        self.shadow.lower()

    def _update_shadow_style(self):
        t = DesignTokens.get(Config.color_scheme)
        self.shadow.setStyleSheet(f"""
            QFrame {{
                background-color: {t['surface']};
                border-radius: 20px;
                border: 2px solid {t['border']};
            }}
        """)

    # ═══════════════════════════════════════════════════════════════
    # 动画
    # ═══════════════════════════════════════════════════════════════

    def animate_result(self, selected: str):
        """抽取结果动画（颜色渐变 + 透明度，OutCubic 缓出）"""
        t = DesignTokens.get(Config.color_scheme)
        self.result_label.setText(selected)
        self.result_label.setFont(Config.get_font(Config.RESULT_FONT_SIZE, bold=True))
        self.result_label.setStyleSheet(
            f"color: {t['result_gold']}; background: transparent;"
        )

        effect = QGraphicsOpacityEffect(self.result_label)
        self.result_label.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(Config.ANIMATION_DURATION)
        animation.setStartValue(Config.ANIMATION_OPACITY_START)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.finished.connect(lambda: self.finalize_animation(selected))
        animation.start()
        self._result_animation = animation

    def finalize_animation(self, selected: str):
        self.status_label.setText("")

    # ═══════════════════════════════════════════════════════════════
    # 抽取流程
    # ═══════════════════════════════════════════════════════════════

    def start_draw_process(self):
        """开始抽取"""
        if self._flash is not None:
            return
        if self.sound_enabled:
            SoundManager.play_start()
        if self.fast_mode_enabled:
            self.perform_draw()
        else:
            self.status_label.setText("抽取中...")
            self._flash = FlashAnimation(
                self.students,
                on_name=self.result_label.setText,
                on_finish=self.perform_draw,
                on_tick=(lambda: SoundManager.play_flash_tick()) if self.sound_enabled else None,
            )
            self._flash.start()

    def perform_draw(self):
        self._flash = None
        probabilities = self.calculate_probabilities()
        student_list, weights = zip(*probabilities.items())
        student_list, weights = list(student_list), list(weights)
        selected = random.choices(student_list, weights=weights, k=1)[0]
        self.stats[selected] = self.stats.get(selected, 0) + 1
        self._add_history_record([selected])
        self._save_stats()
        self._probabilities_cache = None

        if self.sound_enabled:
            SoundManager.play_result()

        self.animate_result(selected)

    def calculate_probabilities(self) -> dict:
        if self._probabilities_cache is None:
            probs = {
                student: 1 / (len(self.students) * (self.stats.get(student, 0) + 1))
                for student in self.students
            }
            total = sum(probs.values())
            if total > 0:
                probs = {k: v / total for k, v in probs.items()}
            self._probabilities_cache = probs
        return self._probabilities_cache

    def ensure_statistics_initialized(self):
        student_set = set(self.students)
        stat_keys = set(self.stats.keys())
        for s in student_set - stat_keys:
            self.stats[s] = 0
        for s in stat_keys - student_set:
            del self.stats[s]
        if student_set != stat_keys:
            self._save_stats()

    # ═══════════════════════════════════════════════════════════════
    # Toast
    # ═══════════════════════════════════════════════════════════════

    def show_toast(self, message: str, duration: int = 2000):
        """显示 Toast 消息（淡入动画）"""
        try:
            if hasattr(self, '_toast') and self._toast is not None:
                self._toast.deleteLater()
        except RuntimeError:
            pass

        toast = QLabel(message, self)
        toast.setObjectName("toast")
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.adjustSize()
        x = (self.width() - toast.width()) // 2
        y = (self.height() - toast.height()) // 2
        toast.move(x, y)
        toast.show()
        self._toast = toast

        effect = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(effect)
        fade = QPropertyAnimation(effect, b"opacity")
        fade.setDuration(Config.TOAST_FADE_DURATION)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        fade.start()
        self._toast_animation = fade

        QTimer.singleShot(duration, toast.deleteLater)

    # ═══════════════════════════════════════════════════════════════
    # 右键菜单
    # ═══════════════════════════════════════════════════════════════

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        # ── 名单 ──
        menu.addAction("导入名单", self.import_student_list)
        menu.addSeparator()

        # ── 统计 ──
        stats_menu = QMenu("统计", self)
        stats_menu.addAction("查看统计信息", self.show_statistics)
        stats_menu.addAction("查看抽取历史", self._show_history_dialog)
        stats_menu.addAction("清除抽取历史", self._clear_history)
        stats_menu.addSeparator()
        stats_menu.addAction("重置数据", self._confirm_reset_stats)
        stats_menu.addAction("导出统计数据", self.export_statistics)
        menu.addMenu(stats_menu)

        # ── 配色方案 ──
        color_menu = QMenu("配色方案", self)
        for key, name in DesignTokens.list_schemes():
            action = color_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(key == Config.color_scheme)
            action.setData(key)
        menu.addMenu(color_menu)

        menu.addSeparator()

        # ── 底部 ──
        menu.addAction("快捷键说明", self._show_shortcuts)
        menu.addAction("关于软件", self.show_about_dialog)
        menu.addSeparator()
        menu.addAction("关闭程序", self.close)

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if not action:
            return
        if action.data() is not None:
            self._apply_color_scheme(action.data())

    def _confirm_reset_stats(self):
        reply = QMessageBox.question(self, "确认重置", "是否确认重置所有统计数据？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stats = {}
            self._probabilities_cache = None
            self.ensure_statistics_initialized()
            self._save_stats()
            self.show_toast("统计数据已重置")

    def _show_shortcuts(self):
        QMessageBox.information(self, "快捷键说明",
            "Space / Enter — 抽取\n"
            "Esc — 最小化到悬浮球\n"
            "Ctrl+T — 切换配色方案\n\n"
            "右键点击窗口可打开完整菜单")

    # ═══════════════════════════════════════════════════════════════
    # 对话框工厂 (P1-4: 消除统计/历史对话框重复)
    # ═══════════════════════════════════════════════════════════════

    def _build_table_dialog(
        self, title: str, headers: list, row_data: list,
        summary_text: str, actions: list, offset: tuple,
        width: int = 500, height: int = 420
    ):
        """通用表格对话框工厂 (P1-4)

        Args:
            title: 对话框标题
            headers: 列标题列表
            row_data: 每行是一个列表，每个单元格为 (value, alignment, bg_color) 元组
            summary_text: 摘要文本
            actions: [(label, callback, style_str), ...] 操作按钮（不包含关闭按钮，关闭按钮自动添加）
            offset: 对话框相对于主窗口的 (dx, dy) 偏移
        """
        t = DesignTokens.get(Config.color_scheme)
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(width, height)
        dlg.setStyleSheet(f"QDialog {{ background: {t['surface_solid']}; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 摘要
        summary = QLabel(summary_text)
        summary.setFont(Config.get_font(10))
        summary.setStyleSheet(f"color: {t['text_secondary']}; background: transparent; padding: 4px 0;")
        layout.addWidget(summary)

        # 表格
        col_count = len(headers)
        table = QTableWidget(len(row_data), col_count)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for ci in range(1, col_count):
            table.horizontalHeader().setSectionResizeMode(ci, QHeaderView.Fixed)
            if ci == 1:
                table.setColumnWidth(ci, 100)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(False)

        for ri, row in enumerate(row_data):
            for ci, (value, align, bg) in enumerate(row):
                item = QTableWidgetItem(str(value))
                if align:
                    item.setTextAlignment(align)
                if bg:
                    item.setBackground(QColor(bg))
                table.setItem(ri, ci, item)

        layout.addWidget(table)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        bw, bh = Config.DIALOG_BTN_SIZE
        for label, slot, style_str in actions:
            btn = QPushButton(label)
            btn.setFixedSize(bw, bh)
            btn.clicked.connect(slot)
            btn.setStyleSheet(f"""
                QPushButton {{ {style_str} border:none; border-radius:8px; font-size:14px; }}
                QPushButton:hover {{ opacity: 0.85; }}
            """)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        # 自动添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(bw, bh)
        close_btn.clicked.connect(dlg.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background:{t['primary']}; color:{t['on_primary']};
            border:none; border-radius:8px; font-size:14px; }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dlg.move(self.x() + offset[0], self.y() + offset[1])
        return dlg

    # ═══════════════════════════════════════════════════════════════
    # 对话框
    # ═══════════════════════════════════════════════════════════════

    def show_about_dialog(self):
        about_box = QMessageBox(self)
        about_box.setWindowTitle("关于软件")
        about_box.setText("Check-number v9.0\n\n"
                          "作者：Soup_007\n如有建议请联系开发者\n"
                          "Mail:750173212@qq.com\n© 2023-2025\n\n"
                          "设计系统：Impeccable × UI UX Pro Max（浅色模式）")
        about_box.setIcon(QMessageBox.Information)
        changelog_btn = about_box.addButton("更新日志", QMessageBox.ActionRole)
        ok_btn = about_box.addButton(QMessageBox.Ok)
        about_box.setDefaultButton(ok_btn)

        def show_changelog():
            try:
                with open("whs_update", "r", encoding="utf-8") as f:
                    changelog = f.read()
            except Exception:
                changelog = "未找到更新日志文件 whs_update。"
            QMessageBox.information(self, "更新日志", changelog)
        changelog_btn.clicked.connect(show_changelog)
        about_box.exec_()

    def show_statistics(self):
        """统计弹窗（使用对话框工厂）"""
        t = DesignTokens.get(Config.color_scheme)
        total_draws = sum(self.stats.values())
        top_student = max(self.stats, key=self.stats.get, default="—")
        top_count = self.stats.get(top_student, 0)
        summary = (
            f"共 {len(self.students)} 名学生  |  总抽取 {total_draws} 次  "
            f"|  最高频: {top_student} ({top_count}次)"
        )

        sorted_students = sorted(self.students, key=lambda s: self.stats.get(s, 0), reverse=True)
        row_data = []
        for i, student in enumerate(sorted_students):
            count = self.stats.get(student, 0)
            bg = None
            if i == 0 and count > 0:
                bg = t['table_gold']
            elif i == 1 and count > 0:
                bg = t['table_silver']
            elif i == 2 and count > 0:
                bg = t['table_bronze']
            row_data.append([
                (str(student), None, bg),
                (f"{count} 次", Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, bg),
            ])

        actions = [
            ("导出", self.export_statistics,
             f"background:{t['btn_min_bg']};color:{t['text_primary']};"),
            ("重置", self._confirm_reset_stats,
             f"background:{t['btn_min_bg']};color:{t['error']};"),
        ]

        dlg = self._build_table_dialog(
            "抽取统计", ["学生", "抽取次数"], row_data,
            summary, actions, Config.STATS_DIALOG_OFFSET,
            width=380, height=440
        )
        dlg.exec_()

    def export_statistics(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出统计数据", "statistics.json", "JSON Files (*.json)"
        )
        if path:
            if self._write_json(path, self.stats):
                self.show_toast("统计数据已导出")
            else:
                self.show_toast("导出失败")

    # ═══════════════════════════════════════════════════════════════
    # 抽取历史
    # ═══════════════════════════════════════════════════════════════

    def _show_history_dialog(self):
        """显示抽取历史对话框（使用对话框工厂）"""
        t = DesignTokens.get(Config.color_scheme)
        history = self._load_history()
        summary = f"共 {len(history)} 条记录"

        row_data = []
        for record in reversed(history):
            ts = record.get("timestamp", "")[:19].replace("T", " ")
            mode = "多人" if record.get("mode") == "multi" else "单人"
            results = "、".join(record.get("results", []))
            row_data.append([
                (ts, None, None),
                (mode, Qt.AlignmentFlag.AlignCenter, None),
                (results, None, None),
            ])

        dlg = self._build_table_dialog(
            "抽取历史记录", ["时间", "模式", "结果"], row_data,
            summary, [], Config.HISTORY_DIALOG_OFFSET,
            width=500, height=420
        )

        # 在关闭按钮前插入"清除历史"按钮
        # _build_table_dialog 创建的按钮栏格式：[stretch, close_btn]
        btn_layout = dlg.layout().itemAt(dlg.layout().count() - 1).layout()
        # 从后往前移除两项，然后按 clear_btn + stretch + close_btn 重新插入
        close_btn_item = btn_layout.takeAt(btn_layout.count() - 1)   # index 1: close button
        stretch_item = btn_layout.takeAt(btn_layout.count() - 1)     # index 0: stretch

        clear_btn = QPushButton("清除历史")
        bw, bh = Config.DIALOG_BTN_SIZE
        clear_btn.setFixedSize(bw, bh)
        clear_btn.clicked.connect(lambda: self._clear_history_from_dialog(dlg))
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background:{t['btn_min_bg']}; color:{t['error']};
            border:none; border-radius:8px; font-size:14px; }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        btn_layout.addWidget(clear_btn)
        btn_layout.addItem(stretch_item)
        btn_layout.addItem(close_btn_item)

        dlg.exec_()

    def _clear_history(self):
        reply = QMessageBox.question(self, "确认清除", "是否清除所有抽取历史记录？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.draw_history = []
            self._save_history()
            self.show_toast("历史记录已清除")

    def _clear_history_from_dialog(self, dialog):
        self.draw_history = []
        self._save_history()
        dialog.accept()
        self.show_toast("历史记录已清除")

    # ═══════════════════════════════════════════════════════════════
    # 音效
    # ═══════════════════════════════════════════════════════════════

    def _toggle_sound(self, enabled: bool):
        """切换音效 (P1-2: 使用 Config.set_sound_enabled)"""
        self.sound_enabled = enabled
        Config.set_sound_enabled(enabled)
        self.show_toast("音效已开启" if enabled else "音效已关闭")

    # ═══════════════════════════════════════════════════════════════
    # 快速模式
    # ═══════════════════════════════════════════════════════════════

    def _toggle_fast_mode(self):
        self.fast_mode_enabled = not self.fast_mode_enabled
        self._update_fast_btn_style()
        self.show_toast("快速模式已开启" if self.fast_mode_enabled else "快速模式已关闭")

    def _update_fast_btn_style(self):
        """更新快速模式按钮样式 (P2-4: 使用 DesignTokens success 颜色)"""
        t = DesignTokens.get(Config.color_scheme)
        if self.fast_mode_enabled:
            self.fast_btn.setStyleSheet(
                f"QPushButton {{ background-color: {t['success']}; border: none; "
                f"border-radius: 7px; min-width: 14px; max-width: 14px; "
                f"min-height: 14px; max-height: 14px; }}"
                f"QPushButton:hover {{ background-color: {t['success']}; opacity: 0.85; }}"
            )
            self.fast_btn.setToolTip("快速模式 — 开启")
        else:
            self.fast_btn.setStyleSheet("")  # 使用 QSS 默认黄色
            self.fast_btn.setToolTip("快速模式 — 关闭")

    def _position_overlays(self):
        """定位悬浮元素 (P2-3: 使用 Config 常量)"""
        w = self.central_widget.width()
        h = self.central_widget.height()
        m = Config.FAST_BTN_MARGIN
        self.fast_btn.move(w - m, h - m)
        self.status_label.setGeometry(0, h - Config.STATUS_LABEL_HEIGHT - 4, w, Config.STATUS_LABEL_HEIGHT)

    # ═══════════════════════════════════════════════════════════════
    # 窗口管理
    # ═══════════════════════════════════════════════════════════════

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_active:
            self._drag_active = False
            Config.set_window_position(self.x(), self.y())
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """双击主界面触发抽取"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_draw_process()
            event.accept()
        super().mouseDoubleClickEvent(event)

    # ── 最小化到悬浮球 ──

    def minimize_to_float(self):
        """最小化到悬浮球 (P1-7: 重命名自 showMinimized，避免覆盖 Qt 语义)"""
        self.hide()
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            x = geometry.width() - Config.FLOAT_SIZE - Config.FLOAT_OFFSET_X
            y = (geometry.height() - Config.FLOAT_SIZE) * 3 // 5
            self.float_window.move(x, y)
            self.float_window.show()

    # 保留 showMinimized 以兼容 Qt 内部调用（委托到 minimize_to_float）
    def showMinimized(self):
        self.minimize_to_float()

    def restore_from_float(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.float_window.hide()

    def closeEvent(self, event):
        """关闭窗口时清理 (P1-2: 使用 Config.set_window_position)"""
        Config.set_window_position(self.x(), self.y())
        if self._flash:
            self._flash.stop()
        self.float_window.close()
        QApplication.quit()
        event.accept()
