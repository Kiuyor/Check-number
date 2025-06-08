import sys
import random
import os
import json
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QFileDialog, QMenu, QMessageBox, QDialog, QTextBrowser, QLineEdit,
    QInputDialog, QAction
)
from PyQt5.QtCore import QThread, QTimer, QPropertyAnimation, QStandardPaths, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5 import QtCore

class Config:
    @staticmethod
    def get_base_dir():
        return QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) + "/check number"
    @staticmethod
    def get_student_file():
        return os.path.join(Config.get_base_dir(), "student.txt")
    @staticmethod
    def get_enc_file():
        return os.path.join(Config.get_base_dir(), "names.enc")
    @staticmethod
    def get_temp_file():
        return os.path.join(Config.get_base_dir(), "names_temp.txt")
    PASSWORD = "******"
    @staticmethod
    def get_stats_file():
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        stats_dir = os.path.join(documents, "check number", "stats")
        os.makedirs(stats_dir, exist_ok=True)
        return os.path.join(stats_dir, "stats.json")
    STATS_FILE = get_stats_file.__func__()
    BACKUP_FILE = "students.bak"
    ANIMATION_STEPS = 40
    ANIMATION_DELAY = 0.05
    WINDOW_SIZE = (280, 190)
    MAIN_COLOR = "#1a73e8"
    PRESSED_COLOR = "#1557b0"
    BACKGROUND_ALPHA = 0.6
    RESULT_FONT_SIZE = 48
    NUM_STUDENTS = 60

statistics = {}

def load_statistics():
    """加载统计数据"""
    global statistics
    try:
        with open(Config.STATS_FILE, "r", encoding="utf-8") as file:
            statistics = json.load(file)
    except Exception:
        statistics = {}

def save_statistics():
    """保存统计数据"""
    try:
        with open(Config.STATS_FILE, "w", encoding="utf-8") as file:
            json.dump(statistics, file, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存统计数据失败: {e}")

load_statistics()

class DrawAnimationThread(QThread):
    name_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    def __init__(self, students, fast_mode=False):
        super().__init__()
        self.students = students.copy()
        self._is_running = True
        self.fast_mode = fast_mode
    def run(self):
        """动画线程，非快速模式下闪动学生姓名"""
        if self.fast_mode:
            self.finished_signal.emit()
            return
        for _ in range(Config.ANIMATION_STEPS):
            if not self._is_running:
                break
            temp_number = random.choice(self.students)
            self.name_signal.emit(temp_number)
            QThread.msleep(int(Config.ANIMATION_DELAY * 1000))
        self.finished_signal.emit()
    def stop(self):
        """停止动画线程"""
        self._is_running = False
        self.wait()

class RandomSelectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icon.ico"))
        self._drag_active = False
        self._drag_position = None
        self.students = []
        self.animation_thread = None
        self.prepare_students_file()
        self.setup_ui()
        self.setup_window_properties()
        self.setup_stylesheet()
        self.ensure_statistics_initialized()
    def prepare_students_file(self):
        """加载并加密名单文件，优先 student.txt，解密 names.enc 到临时文件后加载"""
        base_dir = Config.get_base_dir()
        os.makedirs(base_dir, exist_ok=True)
        student_path = Config.get_student_file()
        enc_path = Config.get_enc_file()
        temp_path = Config.get_temp_file()
        if os.path.exists(student_path):
            try:
                with open(student_path, "rb") as f:
                    content = f.read()
                encrypted = self.xor_encrypt_decrypt(content, Config.PASSWORD)
                with open(enc_path, "wb") as f:
                    f.write(encrypted)
                os.remove(student_path)
                self.show_toast("已加密名单并删除原文件")
            except Exception as e:
                self.show_toast(f"名单加密失败: {e}")
        if os.path.exists(enc_path):
            try:
                with open(enc_path, "rb") as f:
                    encrypted = f.read()
                decrypted = self.xor_encrypt_decrypt(encrypted, Config.PASSWORD)
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(decrypted.decode("utf-8"))
                self.load_students(temp_path)
            except Exception as e:
                self.show_toast(f"名单解密失败: {e}")
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass
        else:
            self.students = [str(i) for i in range(1, Config.NUM_STUDENTS + 1)]
            self.show_toast("未找到名单，已恢复默认")
    def load_students(self, file_path=None):
        """加载名单文件到 self.students"""
        path = file_path
        students = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name:
                        students.append(name)
        except Exception as e:
            self.show_toast(f"名单读取失败: {e}")
        if students:
            self.students = students
            self.ensure_statistics_initialized()
            self.show_toast(f"名单已加载（共{len(students)}人）")
        else:
            self.students = [str(i) for i in range(1, Config.NUM_STUDENTS + 1)]
            self.show_toast("名单为空，已恢复默认")
    def reload_students(self):
        """重新加载名单"""
        self.load_students()
    def import_students(self):
        pass  # 已废弃，不再需要导入名单功能
    def save_last_students_path(self, path):
        """保存最近一次导入名单的路径"""
        try:
            with open("last_students_path.txt", "w", encoding="utf-8") as f:
                f.write(path)
        except Exception:
            pass
    def get_last_students_path(self):
        """获取最近一次导入名单的路径"""
        try:
            with open("last_students_path.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None
    def setup_ui(self):
        """初始化主界面UI"""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.result_label = QLabel("点击抽取", self)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Microsoft YaHei", Config.RESULT_FONT_SIZE, QFont.Bold))
        self.result_label.setMinimumHeight(100)
        self.result_label.setMaximumHeight(120)
        self.main_layout.addWidget(self.result_label)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 12))
        self.main_layout.addWidget(self.status_label)
        btn_layout = QHBoxLayout()
        self.min_btn = QPushButton("—", self)
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #e3e6ea;
                color: #1a73e8;
                border: none;
                border-radius: 14px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: #d2d7de;
            }}
        """)
        self.min_btn.clicked.connect(self.showMinimized)
        btn_layout.addWidget(self.min_btn)
        self.draw_button = QPushButton("抽取", self)
        self.draw_button.setFixedHeight(40)
        self.draw_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Config.MAIN_COLOR};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {Config.PRESSED_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {Config.PRESSED_COLOR};
            }}
        """)
        btn_layout.addWidget(self.draw_button)
        self.main_layout.addLayout(btn_layout)
        self.fast_mode_checkbox = QCheckBox("快速模式")
        self.fast_mode_checkbox.setChecked(False)
        self.draw_button.clicked.connect(self.start_draw_process)
        self.float_window = QPushButton("▶", None)
        self.float_window.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.float_window.setFixedSize(40, 40)
        self.float_window.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 22px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        self.float_window.clicked.connect(self.restore_from_float)
        self.float_window.hide()
    def setup_window_properties(self):
        """设置窗口属性和初始位置"""
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            width, height = Config.WINDOW_SIZE
            x = geometry.width() - width - 20
            y = (geometry.height() - height) // 2
            self.setGeometry(x, y, width, height)
            self.setFixedSize(width, height)
        self.shadow = QFrame(self.central_widget)
        self.shadow.setGeometry(0, 0, width, height)
        self.shadow.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(26, 115, 232, {Config.BACKGROUND_ALPHA});
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        self.shadow.lower()
    def setup_stylesheet(self):
        """设置全局字体和样式"""
        try:
            app_font = QFont("Microsoft YaHei", 11)
        except:
            app_font = QFont("SimSun", 11)
        QApplication.setFont(app_font)
        self.setStyleSheet("")
    def animate_result(self, selected):
        """抽取结果动画"""
        self.result_label.setText(selected)
        animation = QPropertyAnimation(self.result_label, b"windowOpacity")
        animation.setDuration(400)
        animation.setStartValue(0.3)
        animation.setEndValue(1.0)
        animation.finished.connect(lambda: self.finalize_animation(selected))
        animation.start()
        self._animation = animation
    def finalize_animation(self, selected):
        """动画结束后恢复按钮状态"""
        self.draw_button.setEnabled(True)
        self.status_label.setText("")
    def start_draw_process(self):
        """开始抽取流程"""
        self.draw_button.setEnabled(False)
        if self.fast_mode_checkbox.isChecked():
            self.perform_draw()
        else:
            self.status_label.setText("抽取中...")
            self.start_animation()
    def start_animation(self):
        """启动动画线程"""
        if self.animation_thread and self.animation_thread.isRunning():
            return
        self.animation_thread = DrawAnimationThread(self.students, fast_mode=False)
        self.animation_thread.name_signal.connect(self.result_label.setText)
        self.animation_thread.finished_signal.connect(self.perform_draw)
        self.animation_thread.start()
    def perform_draw(self):
        """执行抽取逻辑并保存统计"""
        probabilities = self.calculate_probabilities()
        student_list = list(probabilities.keys())
        weights = list(probabilities.values())
        selected = random.choices(student_list, weights=weights, k=1)[0]
        statistics[selected] = statistics.get(selected, 0) + 1
        save_statistics()
        self.animate_result(selected)
        delattr(self, '_probabilities_cache')
    def calculate_probabilities(self):
        """计算每个学生被抽取的概率"""
        if not hasattr(self, '_probabilities_cache'):
            total_draws = sum(statistics.values())
            probs = {
                student: 1 / (Config.NUM_STUDENTS * (statistics[student] + 1))
                for student in self.students
            }
            total = sum(probs.values())
            if total > 0:
                probs = {k: v / total for k, v in probs.items()}
            self._probabilities_cache = probs
        return self._probabilities_cache
    def ensure_statistics_initialized(self):
        """初始化或同步统计数据"""
        changed = False
        for student in self.students:
            if student not in statistics:
                statistics[student] = 0
                changed = True
        for key in list(statistics.keys()):
            if key not in self.students:
                del statistics[key]
                changed = True
        if changed:
            save_statistics()
    def show_toast(self, message, duration=2000):
        """显示临时提示消息"""
        try:
            if hasattr(self, '_toast') and self._toast is not None:
                self._toast.deleteLater()
        except RuntimeError:
            pass
        toast = QLabel(message, self)
        toast.setStyleSheet("""
            QLabel {
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 16px;
            }
        """)
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.adjustSize()
        x = (self.width() - toast.width()) // 2
        y = (self.height() - toast.height()) // 2
        toast.move(x, y)
        toast.show()
        self._toast = toast
        QTimer.singleShot(duration, toast.deleteLater)
    def xor_encrypt_decrypt(self, data: bytes, key: str) -> bytes:
        """简单异或加解密"""
        key_bytes = key.encode('utf-8')
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])
    def create_example_students(self):
        """生成加密的示例名单文件"""
        example = [f"姓名{i}" for i in range(1, 61)]
        content = '\n'.join(example).encode('utf-8')
        encrypted = self.xor_encrypt_decrypt(content, "250607")
        enc_path = os.path.join(os.getcwd(), "students_example.enc")
        try:
            with open(enc_path, 'wb') as f:
                f.write(encrypted)
            self.show_toast(f"加密示例名单已生成: {enc_path}")
        except Exception as e:
            self.show_toast(f"生成失败: {e}")
    def use_example_students(self):
        """解密示例名单到 students.txt 并加载"""
        enc_path = os.path.join(os.getcwd(), "students_example.enc")
        temp_path = os.path.join(os.getcwd(), "students.txt")
        try:
            with open(enc_path, 'rb') as f:
                encrypted = f.read()
            decrypted = self.xor_encrypt_decrypt(encrypted, "250607")
            with open(temp_path, 'wb') as f:
                f.write(decrypted)
            self.show_toast("示例名单已解密到 students.txt")
            self.load_students(temp_path)
        except Exception as e:
            self.show_toast(f"解密失败: {e}")
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
    def check_students_password(self):
        """校验名单操作密码"""
        pwd, ok = QInputDialog.getText(self, "密码验证", "请输入名单操作密码：", QLineEdit.Password)
        if not ok:
            return False
        if pwd == Config.PASSWORD:
            return True
        QMessageBox.warning(self, "密码错误", "密码错误，操作已取消！")
        return False
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        menu = QMenu(self)
        minimize_action = menu.addAction("最小化窗口")
        close_action = menu.addAction("关闭窗口")
        menu.addSeparator()
        # 移除名单菜单
        stats_menu = QMenu("统计", self)
        view_stats_action = stats_menu.addAction("查看统计信息")
        reset_stats_action = stats_menu.addAction("重置统计")
        export_stats_action = stats_menu.addAction("导出统计数据")
        menu.addMenu(stats_menu)
        settings_menu = QMenu("设置", self)
        fast_mode_action = QAction(self.fast_mode_checkbox.text(), self)
        fast_mode_action.setCheckable(True)
        fast_mode_action.setChecked(self.fast_mode_checkbox.isChecked())
        settings_menu.addAction(fast_mode_action)
        menu.addMenu(settings_menu)
        menu.addSeparator()
        about_action = menu.addAction("关于软件")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == minimize_action:
            self.showMinimized()
        elif action == close_action:
            self.close()
        elif action == reset_stats_action:
            reply = QMessageBox.question(self, "确认重置", 
                                       "是否确认重置所有统计数据？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                global statistics
                statistics = {}
                self.ensure_statistics_initialized()
                save_statistics()
                self.show_toast("统计数据已重置")
        elif action == export_stats_action:
            self.export_statistics()
        elif action == view_stats_action:
            self.show_statistics()
        elif action == fast_mode_action:
            self.fast_mode_checkbox.setChecked(fast_mode_action.isChecked())
        elif action == about_action:
            self.show_about_dialog()
    def show_about_dialog(self):
        """显示关于窗口和更新日志"""
        about_box = QMessageBox(self)
        about_box.setWindowTitle("关于软件")
        about_box.setText("Check-number v8.0\n\n作者：Soup_007\n如有建议请联系开发者\nMail:750173212@qq.com\n© 2023-2025")
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
    def mousePressEvent(self, event):
        """支持窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        """拖动窗口时移动"""
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        """拖动结束"""
        self._drag_active = False
        super().mouseReleaseEvent(event)
    def showMinimized(self):
        """最小化到屏幕右侧悬浮窗"""
        self.hide()
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            x = geometry.width() - 60
            y = (geometry.height() - 40) // 2
            self.float_window.move(x, y)
            self.float_window.show()
    def restore_from_float(self):
        """从悬浮窗恢复主窗口"""
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.float_window.hide()
    def closeEvent(self, event):
        """关闭窗口时清理"""
        self.float_window.close()
        QApplication.quit()
        event.accept()
    def export_statistics(self):
        """导出统计数据为 JSON 文件"""
        path, _ = QFileDialog.getSaveFileName(self, "导出统计数据", f"statistics.json", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(statistics, f, ensure_ascii=False, indent=2)
                self.show_toast("统计数据已导出")
            except Exception as e:
                self.show_toast(f"导出失败: {e}")
    def show_statistics(self):
        """显示统计信息弹窗"""
        info = ""
        for student in self.students:
            count = statistics.get(student, 0)
            info += f"<tr><td style='padding:4px 16px;text-align:left'>{student}</td><td style='padding:4px 16px;text-align:right'>{count} 次</td></tr>"
        if not info:
            info = "<tr><td colspan='2'>暂无统计数据</td></tr>"
        html = f"""
        <html><head><style>
        table {{border-collapse:collapse;font-size:16px;}}
        th,td {{border-bottom:1px solid #e3e6ea;}}
        th {{background:#f5f7fa;font-weight:bold;}}
        </style></head><body>
        <table width='100%'>
        <tr><th>学生</th><th>抽取次数</th></tr>
        {info}
        </table>
        </body></html>
        """
        dlg = QDialog(self)
        dlg.setWindowTitle("抽取统计")
        dlg.setMinimumWidth(340)
        dlg.setMaximumWidth(400)
        dlg.setMinimumHeight(320)
        dlg.setMaximumHeight(480)
        layout = QVBoxLayout(dlg)
        text = QTextBrowser(dlg)
        text.setHtml(html)
        text.setOpenExternalLinks(False)
        text.setStyleSheet("border:none;background:transparent;")
        text.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        layout.addWidget(text)
        btn = QPushButton("关闭", dlg)
        btn.clicked.connect(dlg.accept)
        btn.setFixedSize(120, 36)
        btn.setStyleSheet("margin-top:12px;font-size:16px;border-radius:8px;background:#e3e6ea;color:#1a73e8;")
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        dlg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RandomSelectorWindow()
    window.show()
    sys.exit(app.exec_())
