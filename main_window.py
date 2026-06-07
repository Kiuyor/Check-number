"""
随机点名器 v9.0 — 主窗口
基于加权概率的随机抽取工具，根据历史抽取次数动态调整概率。
"""
import random
import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMenu, QMessageBox, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QGraphicsOpacityEffect,
    QShortcut, QAbstractItemView, QSlider, QTextEdit,
)
from PyQt5.QtCore import (
    QTimer, QPropertyAnimation, Qt, QEasingCurve,
)
from PyQt5.QtGui import QColor, QKeySequence
from design_tokens import DesignTokens
from config import Config
from student_manager import StudentManager
from stats_manager import StatisticsManager
from history_manager import HistoryManager
from flash_animation import FlashAnimation
from sound_manager import SoundManager
from float_ball import FloatBall


class RandomSelectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ── 管理器（P1-11: 职责拆分） ──
        self.student_mgr = StudentManager()
        self.stats_mgr = StatisticsManager()
        self.history_mgr = HistoryManager()

        # ── 状态 ──
        self._drag_active = False
        self._drag_position = None
        self.students: list = []
        self._toast = None
        self._toast_animation = None
        self._flash = None
        self._result_animation = None  # 保持引用防止被 GC

        # ── 功能状态 ──
        self.fast_mode_enabled = False

        # ── 初始化 ──
        self.setup_ui()
        self.setup_window_properties()
        self._apply_theme()
        self.setup_shortcuts()

        # 延迟 I/O，让窗口先显示
        QTimer.singleShot(0, self._deferred_init)

    # ═══════════════════════════════════════════════════════════════
    # 延迟初始化
    # ═══════════════════════════════════════════════════════════════

    def _deferred_init(self):
        """窗口显示后加载数据 (P1-6: 防止 I/O 异常导致空名单)"""
        try:
            self.stats_mgr.load_from_json()
            self.history_mgr.load_from_json()
            students, messages = self.student_mgr.prepare_students_file()
            self.students = students
            self.stats_mgr.ensure_initialized(self.students)
            for msg in messages:
                self.show_toast(msg)
        except Exception as e:
            print(f"[MainWindow] 数据加载失败: {e}", file=sys.stderr)
            self.show_toast(f"数据加载失败: {e}")

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

    def _apply_window_opacity(self, value: float):
        """应用窗口卡片透明度，持久化并刷新"""
        Config.set_window_opacity(value)
        self._update_shadow_style()
        pct = int(value * 100)
        self.show_toast(f"透明度：{pct}%")

    def _apply_font_family(self, family: str):
        """应用显示字体，刷新全局和组件字体"""
        Config.set_font_family(family)
        QApplication.instance().setFont(Config.get_font(11))
        self._refresh_fonts()
        self.show_toast(f"字体：{family}")

    def _refresh_fonts(self):
        """重新应用已显式设置字体的组件（字体族切换时调用）"""
        self.result_label.setFont(Config.get_font(Config.RESULT_FONT_SIZE, bold=True))
        self.status_label.setFont(Config.get_font(11))
        # 悬浮球使用 QSS，不受 qApp 字体影响，无需刷新

    def _build_opacity_dialog(self, title, getter, setter, apply_style, toast_label):
        """通用透明度滑块弹窗工厂 (P1-2: 消除两个 ~95 行弹窗的重复)

        Args:
            title: 对话框标题
            getter: 获取当前值 (→ float)
            setter: 设置值 (value, save)
            apply_style: 实时刷新样式的回调
            toast_label: Toast 消息前缀（如 "透明度" / "小球透明度"）
        """
        t = DesignTokens.get(Config.color_scheme)
        previous = getter()

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setFixedSize(320, 140)
        dlg.setStyleSheet(f"QDialog {{ background: {t['surface_solid']}; border-radius: 12px; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        pct_label = QLabel(f"{int(previous * 100)}%")
        pct_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pct_label.setFont(Config.get_font(18, bold=True))
        pct_label.setStyleSheet(f"color: {t['on_primary']}; background: transparent;")
        layout.addWidget(pct_label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(25, 100)
        slider.setValue(int(previous * 100))
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(5)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {t['btn_min_bg']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t['primary']};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {t['primary']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(slider)

        def _on_slider_change(val):
            pct_label.setText(f"{val}%")
            setter(val / 100.0, save=False)
            apply_style()

        slider.valueChanged.connect(_on_slider_change)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        bw, bh = Config.DIALOG_BTN_SIZE

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(bw, bh)
        cancel_btn.clicked.connect(dlg.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background: {t['btn_min_bg']}; color: {t['text_primary']};
            border: none; border-radius: 8px; font-size: 14px; }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(bw, bh)
        ok_btn.clicked.connect(dlg.accept)
        ok_btn.setStyleSheet(f"""
            QPushButton {{ background: {t['primary']}; color: {t['on_primary']};
            border: none; border-radius: 8px; font-size: 14px; }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        dlg.move(self.x() + (self.width() - 320) // 2,
                 self.y() + (self.height() - 140) // 2)

        result = dlg.exec_()

        if result == QDialog.Accepted:
            final_value = slider.value() / 100.0
            setter(final_value)
            apply_style()
            self.show_toast(f"{toast_label}：{slider.value()}%")
        else:
            setter(previous, save=False)
            apply_style()

    def _apply_ball_opacity(self, value: float):
        """应用悬浮球透明度，持久化并刷新样式"""
        Config.set_ball_opacity(value)
        if hasattr(self, 'float_window') and self.float_window is not None:
            self.float_window.refresh_theme()
        pct = int(value * 100)
        self.show_toast(f"小球透明度：{pct}%")

    def _show_opacity_dialog(self):
        """窗口透明度滑块弹窗"""
        self._build_opacity_dialog(
            "自定义透明度",
            lambda: Config.window_opacity,
            Config.set_window_opacity,
            self._update_shadow_style,
            "透明度",
        )

    def _show_ball_opacity_dialog(self):
        """悬浮球透明度滑块弹窗"""
        self._build_opacity_dialog(
            "自定义小球透明度",
            lambda: Config.ball_opacity,
            Config.set_ball_opacity,
            lambda: self.float_window.refresh_theme() if self.float_window else None,
            "小球透明度",
        )

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
        r, g, b = DesignTokens.get_surface_rgb(Config.color_scheme)
        alpha = Config.window_opacity
        self.shadow.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({r}, {g}, {b}, {alpha:.2f});
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
        if Config.sound_enabled:
            SoundManager.play_start()
        if self.fast_mode_enabled:
            self.perform_draw()
        else:
            self.status_label.setText("抽取中...")
            self._flash = FlashAnimation(
                self.students,
                on_name=self.result_label.setText,
                on_finish=self.perform_draw,
                on_tick=(lambda: SoundManager.play_flash_tick()) if Config.sound_enabled else None,
            )
            self._flash.start()

    def perform_draw(self):
        self._flash = None
        probabilities = self.stats_mgr.calculate_probabilities(self.students)
        student_list, weights = zip(*probabilities.items())
        student_list, weights = list(student_list), list(weights)
        selected = random.choices(student_list, weights=weights, k=1)[0]
        self.stats_mgr.increment(selected)
        self.history_mgr.add_record([selected])

        if Config.sound_enabled:
            SoundManager.play_result()

        self.animate_result(selected)

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

    def _build_checkable_menu(self, title: str, items: list, current_value, tag: str) -> QMenu:
        """构建可复选的子菜单（P1-5: 消除 contextMenuEvent 中子菜单重复构建）

        Args:
            title: 菜单标题
            items: [(label, value), ...]
            current_value: 当前选中值
            tag: action.data() 中存储的标签（如 "scheme", "window_opacity"）
        """
        menu = QMenu(title, self)
        for label, val in items:
            action = menu.addAction(label)
            action.setCheckable(True)
            if isinstance(current_value, float):
                action.setChecked(abs(current_value - val) < 0.01)
            else:
                action.setChecked(current_value == val)
            action.setData((tag, val))
        return menu

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        # ── 名单 ──
        menu.addAction("导入名单", self._import_student_list)
        menu.addSeparator()

        # ── 统计 ──
        stats_menu = QMenu("统计", self)
        stats_menu.addAction("查看统计信息", self.show_statistics)
        stats_menu.addAction("查看抽取历史", self._show_history_dialog)
        stats_menu.addAction("清除抽取历史", self._clear_history)
        stats_menu.addSeparator()
        stats_menu.addAction("重置数据", self._confirm_reset_stats)
        stats_menu.addAction("导出统计数据", self._export_stats)
        menu.addMenu(stats_menu)

        # ── 配色方案 ──
        scheme_items = [(name, key) for key, name in DesignTokens.list_schemes()]
        menu.addMenu(self._build_checkable_menu("配色方案", scheme_items, Config.color_scheme, "scheme"))

        # ── 窗口透明度 ──
        opacity_presets = [
            ("极透明", 0.30), ("高透明", 0.45), ("默认", 0.60),
            ("低透明", 0.75), ("微透明", 0.90),
        ]
        opacity_menu = self._build_checkable_menu("窗口透明度", opacity_presets, Config.window_opacity, "window_opacity")
        opacity_menu.addSeparator()
        opacity_menu.addAction("自定义...", self._show_opacity_dialog)
        menu.addMenu(opacity_menu)

        # ── 显示字体 ──
        font_items = [(f, f) for f in Config.FONT_OPTIONS]
        menu.addMenu(self._build_checkable_menu("显示字体", font_items, Config.font_family, "font"))

        # ── 小球透明度 ──
        ball_presets = [
            ("微透明", 0.30), ("高透明", 0.50), ("默认", 0.70),
            ("低透明", 0.85), ("实心", 1.00),
        ]
        ball_menu = self._build_checkable_menu("小球透明度", ball_presets, Config.ball_opacity, "ball_opacity")
        ball_menu.addSeparator()
        ball_menu.addAction("自定义...", self._show_ball_opacity_dialog)
        menu.addMenu(ball_menu)

        menu.addSeparator()

        # ── 底部 ──
        menu.addAction("快捷键说明", self._show_shortcuts)
        menu.addAction("关于软件", self.show_about_dialog)
        menu.addSeparator()
        menu.addAction("关闭程序", self.close)

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if not action:
            return
        data = action.data()
        if data is not None and isinstance(data, tuple):
            tag, value = data
            if tag == "scheme":
                self._apply_color_scheme(value)
            elif tag == "window_opacity":
                self._apply_window_opacity(value)
            elif tag == "font":
                self._apply_font_family(value)
            elif tag == "ball_opacity":
                self._apply_ball_opacity(value)

    # ── 管理器适配方法（P1-11: 委托给管理器 + Toast 反馈） ──

    def _import_student_list(self):
        """导入名单（委托给 StudentManager）"""
        students, message, reset_stats = self.student_mgr.import_student_list(self)
        if students is None:
            if message:
                self.show_toast(message)
            return
        if reset_stats:
            self.stats_mgr.reset(self)
            self.stats_mgr.ensure_initialized(students)
        self.students = students
        self.show_toast(message)

    def _confirm_reset_stats(self):
        if self.stats_mgr.reset(self):
            self.stats_mgr.ensure_initialized(self.students)
            self.show_toast("统计数据已重置")

    def _export_stats(self):
        if self.stats_mgr.export_json(self):
            self.show_toast("统计数据已导出")
        else:
            self.show_toast("导出失败")

    def _clear_history(self):
        if self.history_mgr.clear(self):
            self.show_toast("历史记录已清除")

    def _clear_history_from_dialog(self, dialog):
        self.history_mgr.clear_from_dialog(dialog)
        self.show_toast("历史记录已清除")

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
        width: int = 500, height: int = 420,
        extra_buttons: list = None,
    ):
        """通用表格对话框工厂 (P1-4)

        Args:
            title: 对话框标题
            headers: 列标题列表
            row_data: 每行是一个列表，每个单元格为 (value, alignment, bg_color) 元组
            summary_text: 摘要文本
            actions: [(label, callback, style_str), ...] 操作按钮
            offset: 对话框相对于主窗口的 (dx, dy) 偏移
            extra_buttons: [(label, callback, style_str), ...] 额外按钮（插在 actions 和 stretch 之间）
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

        # 额外按钮（由调用方插入在 actions 和 stretch 之间）
        if extra_buttons:
            for label, slot, style_str in extra_buttons:
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
        about_box.setText("Check-number v9.2\n\n"
                          "作者：Soup_007\n如有建议请联系开发者\n"
                          "Mail:750173212@qq.com\n© 2023-2025\n\n"
                          "设计系统：Impeccable × UI UX Pro Max（浅色模式）")
        about_box.setIcon(QMessageBox.Information)
        changelog_btn = about_box.addButton("更新日志", QMessageBox.ActionRole)
        ok_btn = about_box.addButton(QMessageBox.Ok)
        about_box.setDefaultButton(ok_btn)

        def show_changelog():
            try:
                # 编译后 CWD 可能不是 exe 所在目录，解析绝对路径
                if getattr(sys, 'frozen', False):
                    base = os.path.dirname(sys.executable)
                else:
                    base = os.path.dirname(os.path.abspath(__file__))
                changelog_path = os.path.join(base, "whs_update")
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog = f.read()
            except Exception:
                changelog = "未找到更新日志文件 whs_update。"
            # 用可滚动的 QTextEdit 替代 QMessageBox（日志过长时不会截断）
            dlg = QDialog(self)
            dlg.setWindowTitle("更新日志")
            dlg.resize(520, 480)
            layout = QVBoxLayout(dlg)
            text = QTextEdit()
            text.setReadOnly(True)
            text.setPlainText(changelog)
            text.setFont(Config.get_font(11))
            layout.addWidget(text)
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dlg.accept)
            close_btn.setFixedSize(80, 32)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            dlg.exec_()
        changelog_btn.clicked.connect(show_changelog)
        about_box.exec_()

    def show_statistics(self):
        """统计弹窗（使用对话框工厂）"""
        t = DesignTokens.get(Config.color_scheme)
        stats = self.stats_mgr.stats
        total_draws = sum(stats.values())
        top_student = max(stats, key=stats.get, default="—")
        top_count = stats.get(top_student, 0)
        summary = (
            f"共 {len(self.students)} 名学生  |  总抽取 {total_draws} 次  "
            f"|  最高频: {top_student} ({top_count}次)"
        )

        sorted_students = sorted(self.students, key=lambda s: stats.get(s, 0), reverse=True)
        row_data = []
        for i, student in enumerate(sorted_students):
            count = stats.get(student, 0)
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
            ("导出", self._export_stats,
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

    # ═══════════════════════════════════════════════════════════════
    # 抽取历史
    # ═══════════════════════════════════════════════════════════════

    def _show_history_dialog(self):
        """显示抽取历史对话框（使用对话框工厂）"""
        t = DesignTokens.get(Config.color_scheme)
        history = self.history_mgr.history
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
            width=500, height=420,
            extra_buttons=[
                ("清除历史", lambda: self._clear_history_from_dialog(dlg),
                 f"background:{t['btn_min_bg']}; color:{t['error']};"),
            ],
        )

        dlg.exec_()



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
