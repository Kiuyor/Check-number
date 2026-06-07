"""
应用配置 — 常量、路径管理、偏好设置、QSS 样式生成。
"""
import os
import sys
import json
from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QFont
from design_tokens import DesignTokens


class Config:
    """应用配置常量与路径管理"""

    # ── XOR 加密密钥 ──
    # P0-1: 优先从环境变量 CHECK_NUMBER_KEY 读取，回退到内置默认值
    PASSWORD = os.environ.get("CHECK_NUMBER_KEY", "******")

    # ── 动画 ──
    ANIMATION_STEPS = 40
    ANIMATION_DELAY = 50   # ms
    ANIMATION_DURATION = 400
    ANIMATION_OPACITY_START = 0.3
    TOAST_FADE_DURATION = 300

    # ── 窗口 ──
    WINDOW_SIZE = (280, 140)        # 默认（单人）窗口尺寸
    WINDOW_MAX_WIDTH = 600          # 多人抽取时窗口最大宽度
    WINDOW_MIN_SIZE = (280, 140)    # 窗口最小尺寸（等同默认）
    WINDOW_H_PAD = 36               # 结果文字左右留白总宽
    WINDOW_MARGIN = 20
    FLOAT_OFFSET_X = 12
    FLOAT_SIZE = 40

    # ── 字体 ──
    RESULT_FONT_SIZE = 48
    FONT_FAMILY = "HarmonyOS Sans"
    FONT_FAMILY_FALLBACK = "SimSun"
    FONT_OPTIONS = ["HarmonyOS Sans", "Inter Display", "Open Sans", "Noto Sans"]

    # ── 默认学生数量 ──
    NUM_STUDENTS = 60

    # ── 概率算法参数（P1-3: 三层公平性保护，硬编码不暴露给用户） ──
    GAP_THRESHOLD = 3            # 最大-最小抽取次数差距超过此值触发平均值过滤
    CANDIDATE_POOL_MIN_RATIO = 0.30  # 候选池不低于总人数的 30%
    COLD_START_FLOOR_RATIO = 0.5     # 冷启动概率下限 = 平均概率 × 此值

    # ── 历史记录 ──
    MAX_HISTORY_RECORDS = 500

    # ── 布局常量 (P2-3: 从 main_window.py 提取的魔法数字) ──
    MIN_BTN_POS = (10, 10)
    FAST_BTN_MARGIN = 24
    STATUS_LABEL_HEIGHT = 18
    DIALOG_BTN_SIZE = (90, 32)
    STATS_DIALOG_OFFSET = (-50, -50)
    HISTORY_DIALOG_OFFSET = (-110, -50)

    # ── 路径缓存 ──
    _BASE_DIR = None
    _STATS_FILE = None
    _CONFIG_FILE = None
    _HISTORY_FILE = None

    # ── 偏好设置 ──
    # 注意：这些类变量是全局可变状态。不要直接赋值，应当使用 set_*() 类方法
    # 以自动触发持久化保存。例外：load_preferences() 在启动时通过直接赋值初始化，
    # 因为此时尚未（也不应）触发保存。
    color_scheme = "sky"
    window_x = None
    window_y = None
    sound_enabled = False
    window_opacity = 0.60  # 窗口卡片透明度 (0.25–1.00)
    ball_opacity = 0.70    # 悬浮球透明度 (0.25–1.00)
    font_family = "HarmonyOS Sans"  # 显示字体

    # ═══════════════════════════════════════════════════════════════
    # 字体工厂
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_font(size: int, bold: bool = False) -> QFont:
        """统一的字体工厂方法 (P2-5)

        所有 UI 组件应通过此方法获取字体，避免内联 QFont(...) 构造。
        """
        weight = QFont.Bold if bold else QFont.Normal
        return QFont(Config.font_family, size, weight)

    # ═══════════════════════════════════════════════════════════════
    # 偏好设置（带错误处理）
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def set_color_scheme(cls, key: str):
        """设置配色方案并自动保存 (P1-2)"""
        cls.color_scheme = key
        cls.save_preferences()

    @classmethod
    def set_sound_enabled(cls, enabled: bool):
        """设置音效开关并自动保存 (P1-2)"""
        cls.sound_enabled = enabled
        cls.save_preferences()

    @classmethod
    def set_window_position(cls, x: int, y: int):
        """设置窗口位置并自动保存 (P1-2)"""
        cls.window_x = x
        cls.window_y = y
        cls.save_preferences()

    @classmethod
    def set_window_opacity(cls, value: float, save: bool = True):
        """设置窗口透明度 (0.25–1.00)，save=False 时仅改内存不写磁盘"""
        cls.window_opacity = max(0.25, min(1.00, float(value)))
        if save:
            cls.save_preferences()

    @classmethod
    def set_ball_opacity(cls, value: float, save: bool = True):
        """设置悬浮球透明度 (0.25–1.00)，save=False 时仅改内存不写磁盘"""
        cls.ball_opacity = max(0.25, min(1.00, float(value)))
        if save:
            cls.save_preferences()

    @classmethod
    def set_font_family(cls, family: str, save: bool = True):
        """设置显示字体，save=False 时仅改内存不写磁盘"""
        cls.font_family = family
        if save:
            cls.save_preferences()

    @staticmethod
    def load_preferences():
        """加载偏好设置 (P0-2: 区分错误类型)"""
        config_path = Config.get_config_file()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                prefs = json.load(f)
            Config.color_scheme = prefs.get("color_scheme", "sky")
            Config.window_x = prefs.get("window_x")
            Config.window_y = prefs.get("window_y")
            Config.sound_enabled = prefs.get("sound_enabled", False)
            Config.window_opacity = max(0.25, min(1.00, float(prefs.get("window_opacity", 0.60))))
            Config.ball_opacity = max(0.25, min(1.00, float(prefs.get("ball_opacity", 0.70))))
            font_family = prefs.get("font_family", "HarmonyOS Sans")
            Config.font_family = font_family if font_family in Config.FONT_OPTIONS else "HarmonyOS Sans"
        except FileNotFoundError:
            # 首次运行，使用默认值 — 无需警告
            pass
        except json.JSONDecodeError as e:
            print(f"[Config] 偏好文件损坏（使用默认值）: {e}", file=sys.stderr)
        except (PermissionError, OSError) as e:
            print(f"[Config] 偏好加载失败（使用默认值）: {e}", file=sys.stderr)

    @staticmethod
    def save_preferences():
        """保存偏好设置 (P0-2: 委托 write_json 使用原子写入)"""
        prefs = {
            "color_scheme": Config.color_scheme,
            "window_x": Config.window_x,
            "window_y": Config.window_y,
            "sound_enabled": Config.sound_enabled,
            "window_opacity": Config.window_opacity,
            "ball_opacity": Config.ball_opacity,
            "font_family": Config.font_family,
        }
        Config.write_json(Config.get_config_file(), prefs)

    # ═══════════════════════════════════════════════════════════════
    # 路径管理
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_base_dir():
        """获取应用数据根目录 (P2-2: 统一使用 os.path.join)"""
        if Config._BASE_DIR is None:
            Config._BASE_DIR = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
                "check number"
            )
        return Config._BASE_DIR

    @staticmethod
    def get_student_file():
        return os.path.join(Config.get_base_dir(), "student.txt")

    @staticmethod
    def get_enc_file():
        return os.path.join(Config.get_base_dir(), "names.enc")

    @staticmethod
    def get_stats_file():
        if Config._STATS_FILE is None:
            documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            stats_dir = os.path.join(documents, "check number", "stats")
            os.makedirs(stats_dir, exist_ok=True)
            Config._STATS_FILE = os.path.join(stats_dir, "stats.json")
        return Config._STATS_FILE

    @staticmethod
    def get_config_file():
        if Config._CONFIG_FILE is None:
            Config._CONFIG_FILE = os.path.join(Config.get_base_dir(), "config.json")
        return Config._CONFIG_FILE

    @staticmethod
    def get_history_file():
        """获取抽取历史文件路径"""
        if Config._HISTORY_FILE is None:
            documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            stats_dir = os.path.join(documents, "check number", "stats")
            os.makedirs(stats_dir, exist_ok=True)
            Config._HISTORY_FILE = os.path.join(stats_dir, "draw_history.json")
        return Config._HISTORY_FILE

    # ═══════════════════════════════════════════════════════════════
    # 共享 JSON 工具 (P1-1: 消除 stats_manager / history_manager 的重复)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def read_json(file_path: str, default):
        """读取 JSON 文件，带错误分类处理。default 是文件不存在时的返回值。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default
        except json.JSONDecodeError as e:
            print(f"[Config] JSON 文件损坏 ({file_path}): {e}", file=sys.stderr)
            try:
                os.rename(file_path, file_path + ".corrupted")
            except OSError:
                pass
            return default
        except (PermissionError, OSError) as e:
            print(f"[Config] 文件读取失败 ({file_path}): {e}", file=sys.stderr)
            return default

    @staticmethod
    def write_json(file_path: str, data) -> bool:
        """写入 JSON 文件（tmp+replace 原子模式），成功返回 True，失败返回 False。"""
        try:
            tmp_path = file_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, file_path)
            return True
        except (PermissionError, OSError) as e:
            print(f"[Config] 文件写入失败 ({file_path}): {e}", file=sys.stderr)
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            return False

    # ═══════════════════════════════════════════════════════════════
    # QSS 样式生成 (P1-6: 拆分为可组合的小方法)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_stylesheet():
        """动态生成全局 QSS（由各组件方法拼装）"""
        t = DesignTokens.get(Config.color_scheme)
        parts = [
            Config._global_qss(),
            Config._button_qss(t),
            Config._mac_button_qss(),
            Config._toast_qss(t),
            Config._menu_qss(t),
            Config._checkbox_qss(t),
            Config._table_qss(t),
            Config._scrollbar_qss(t),
            Config._focus_qss(),
        ]
        return "\n".join(parts)

    @staticmethod
    def _global_qss():
        return """
        /* ── 全局 ── */
        QMainWindow {
            background: transparent;
        }
        """

    @staticmethod
    def _button_qss(t):
        return f"""
        /* ── 抽取按钮 ── */
        QPushButton#drawBtn {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {t['gradient_top']},stop:1 {t['gradient_bottom']});
            color: {t['on_primary']};
            border: none;
            border-radius: 20px;
            font-size: 16px;
            padding: 8px 20px;
        }}
        QPushButton#drawBtn:hover {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {t['primary']},stop:1 {t['primary_hover']});
            border: 2px solid {t['border']};
        }}
        QPushButton#drawBtn:pressed {{
            background: {t['primary_active']};
        }}
        QPushButton#drawBtn:disabled {{
            background: {t['primary_hover']};
            color: rgba(255,255,255,0.5);
        }}
        """

    @staticmethod
    def _mac_button_qss():
        return """
        /* ── macOS 风格红/黄按钮 ── */
        QPushButton#macCloseBtn {
            background-color: #FF5F57;
            border: none;
            border-radius: 7px;
            min-width: 14px;
            max-width: 14px;
            min-height: 14px;
            max-height: 14px;
        }
        QPushButton#macCloseBtn:hover {
            background-color: #FF3B30;
        }
        QPushButton#macFastBtn {
            background-color: #FFBD2E;
            border: none;
            border-radius: 7px;
            min-width: 14px;
            max-width: 14px;
            min-height: 14px;
            max-height: 14px;
        }
        QPushButton#macFastBtn:hover {
            background-color: #FFCC02;
        }
        """

    @staticmethod
    def _toast_qss(t):
        return f"""
        /* ── Toast ── */
        QLabel#toast {{
            background: {t['toast_bg']};
            color: {t['toast_fg']};
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 16px;
        }}
        """

    @staticmethod
    def _menu_qss(t):
        return f"""
        /* ── 右键菜单 ── */
        QMenu {{
            background: {t['surface_solid']};
            color: {t['text_primary']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 28px 6px 16px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background: {t['primary']};
            color: {t['on_primary']};
        }}
        QMenu::separator {{
            height: 1px;
            background: {t['border']};
            margin: 4px 8px;
        }}
        """

    @staticmethod
    def _checkbox_qss(t):
        return f"""
        /* ── 复选框 ── */
        QCheckBox {{
            color: {t['on_primary']};
        }}
        """

    @staticmethod
    def _table_qss(t):
        return f"""
        /* ── 表格 ── */
        QTableWidget {{
            background: transparent;
            border: none;
            gridline-color: {t['table_border']};
            font-size: 14px;
            color: {t['text_primary']};
        }}
        QHeaderView::section {{
            background: {t['table_header']};
            color: {t['text_primary']};
            border: none;
            border-bottom: 2px solid {t['primary']};
            padding: 8px 12px;
        }}
        """

    @staticmethod
    def _scrollbar_qss(t):
        return f"""
        /* ── 滚动条 ── */
        QScrollBar:vertical {{
            background: {t['table_header']};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['primary']};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        """

    @staticmethod
    def _focus_qss():
        return """
        /* ── 焦点 ── */
        QPushButton:focus {
            outline: none;
        }
        """
