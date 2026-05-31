"""
设计 Token（Impeccable Product Register — 保留型色彩策略）
6 套内置配色方案，基于 Impeccable 产品注册表。

合并策略（P2-10 文档化）：
  Token 字典通过三层合并构建：
    1. _DEFAULTS — 所有方案共享的默认值
    2. _BASE_SCHEMES[key] — 方案特定值，可覆盖 _DEFAULTS 中的键
    3. _build_scheme 派生值 — 自动计算的 surface/splash 色
  浅色主题（如 sky）会覆盖 _DEFAULTS 中的 text_primary、border 等以达到足够对比度。
"""
from PyQt5.QtGui import QColor


class DesignTokens:
    """设计 Token — 6 套内置配色方案，基于 Impeccable 产品注册表"""

    # ── 默认值（可被各方案覆盖） ──
    _DEFAULTS = {
        "on_primary": "#FFFFFF",
        "on_surface": "#1E1B4B",
        "text_primary": "#1E1B4B",
        "text_secondary": "#6B7280",
        "border": "rgba(255, 255, 255, 0.15)",
        "result_gold": "#F59E0B",
        "success": "#10B981",
        "error": "#EF4444",
        "toast_bg": "rgba(30, 27, 75, 0.90)",
        "toast_fg": "#FFFFFF",
        "table_gold": "#FEF3C7",
        "table_silver": "#F8FAFC",
        "table_bronze": "#FFF7ED",
    }

    # ── 各配色方案的基础色 ──
    _BASE_SCHEMES = {
        "indigo": {
            "name": "靛蓝",
            "primary": "#4F46E5", "primary_hover": "#4338CA", "primary_active": "#3730A3",
            "gradient_top": "#5B52F0", "gradient_bottom": "#3B3CC4",
            "surface_solid": "#4F46E5", "btn_min_bg": "#E0E7FF",
            "table_header": "#F5F3FF", "table_border": "#E0E7FF",
            "ball_bg": "#4F46E5", "ball_hover": "#4338CA",
            "shadow_color": QColor(0, 0, 0, 50),
        },
        "ocean": {
            "name": "海蓝",
            "primary": "#0EA5E9", "primary_hover": "#0284C7", "primary_active": "#0369A1",
            "gradient_top": "#38BDF8", "gradient_bottom": "#0284C7",
            "surface_solid": "#0EA5E9", "btn_min_bg": "#E0F2FE",
            "table_header": "#F0F9FF", "table_border": "#BAE6FD",
            "ball_bg": "#0EA5E9", "ball_hover": "#0284C7",
            "shadow_color": QColor(0, 0, 0, 50),
        },
        "emerald": {
            "name": "翡翠绿",
            "primary": "#10B981", "primary_hover": "#059669", "primary_active": "#047857",
            "gradient_top": "#34D399", "gradient_bottom": "#059669",
            "surface_solid": "#10B981", "btn_min_bg": "#D1FAE5",
            "table_header": "#ECFDF5", "table_border": "#A7F3D0",
            "ball_bg": "#10B981", "ball_hover": "#059669",
            "shadow_color": QColor(0, 0, 0, 50),
        },
        "sunset": {
            "name": "日落橙",
            "primary": "#F97316", "primary_hover": "#EA580C", "primary_active": "#C2410C",
            "gradient_top": "#FB923C", "gradient_bottom": "#EA580C",
            "surface_solid": "#F97316", "btn_min_bg": "#FFF7ED",
            "table_header": "#FFF7ED", "table_border": "#FFEDD5",
            "ball_bg": "#F97316", "ball_hover": "#EA580C",
            "shadow_color": QColor(0, 0, 0, 50),
        },
        "rose": {
            "name": "玫瑰粉",
            "primary": "#EC4899", "primary_hover": "#DB2777", "primary_active": "#BE185D",
            "gradient_top": "#F472B6", "gradient_bottom": "#DB2777",
            "surface_solid": "#EC4899", "btn_min_bg": "#FCE7F3",
            "table_header": "#FDF2F8", "table_border": "#FBCFE8",
            "ball_bg": "#EC4899", "ball_hover": "#DB2777",
            "shadow_color": QColor(0, 0, 0, 50),
        },
        "violet": {
            "name": "紫罗兰",
            "primary": "#8B5CF6", "primary_hover": "#7C3AED", "primary_active": "#6D28D9",
            "gradient_top": "#A78BFA", "gradient_bottom": "#7C3AED",
            "surface_solid": "#8B5CF6", "btn_min_bg": "#EDE9FE",
            "table_header": "#F5F3FF", "table_border": "#DDD6FE",
            "ball_bg": "#8B5CF6", "ball_hover": "#7C3AED",
            "shadow_color": QColor(0, 0, 0, 50),
        },
        "sky": {
            "name": "晴空蓝",
            "primary": "#2563EB", "primary_hover": "#1D4ED8", "primary_active": "#1E40AF",
            "gradient_top": "#3B82F6", "gradient_bottom": "#1D4ED8",
            "surface_solid": "#F0F9FF", "btn_min_bg": "#DBEAFE",
            "table_header": "#F0F9FF", "table_border": "#BFDBFE",
            "ball_bg": "#2563EB", "ball_hover": "#1D4ED8",
            "shadow_color": QColor(0, 0, 0, 25),
            # 浅色主题覆盖项（覆盖 _DEFAULTS 中默认深色底的值）
            "text_primary": "#0F172A",
            "text_secondary": "#475569",
            "border": "rgba(0, 0, 0, 0.08)",
            "toast_bg": "rgba(15, 23, 42, 0.92)",
            "result_gold": "#000000",
        },
    }

    # ═══════════════════════════════════════════════════════════════
    # 颜色工具
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _srgb_to_linear(c: float) -> float:
        """sRGB 通道值 (0.0–1.0) → 线性亮度分量 (P2-6: 提取复用)"""
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    @staticmethod
    def _hex_to_rgb(hex_color: str):
        """#RRGGBB → (r, g, b) 带输入校验 (P2-8)"""
        if not isinstance(hex_color, str) or not hex_color.startswith("#"):
            raise ValueError(f"非法颜色格式: {hex_color!r}，期望 #RRGGBB")
        h = hex_color.lstrip("#")
        if len(h) != 6:
            raise ValueError(f"非法颜色格式: {hex_color!r}，期望 6 位十六进制")
        try:
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            raise ValueError(f"非法颜色格式: {hex_color!r}，含非十六进制字符")

    # ═══════════════════════════════════════════════════════════════
    # Token 构建与查询
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def _build_scheme(cls, base: dict) -> dict:
        """从基础色推导完整 Token 字典（含自适应 splash 文字色）"""
        r, g, b = cls._hex_to_rgb(base["surface_solid"])
        r_lin = cls._srgb_to_linear(r / 255.0)
        g_lin = cls._srgb_to_linear(g / 255.0)
        b_lin = cls._srgb_to_linear(b / 255.0)
        luminance = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

        derived = {
            "surface": f"rgba({r}, {g}, {b}, 0.60)",
            "btn_min_fg": base["primary"],
        }
        if luminance > 0.5:
            derived["splash_title_fg"] = "#0F172A"
            derived["splash_subtitle_fg"] = "rgba(15,23,42,0.65)"
            derived["splash_dots_fg"] = "rgba(15,23,42,0.40)"
        else:
            derived["splash_title_fg"] = "#FFFFFF"
            derived["splash_subtitle_fg"] = "rgba(255,255,255,0.70)"
            derived["splash_dots_fg"] = "rgba(255,255,255,0.45)"

        # 三层合并：默认值 → 方案覆盖 → 派生值
        return {**cls._DEFAULTS, **base, **derived}

    @classmethod
    def get(cls, scheme_key: str) -> dict:
        """获取指定配色方案的完整 Token 字典"""
        return cls._build_scheme(cls._BASE_SCHEMES[scheme_key])

    @classmethod
    def get_scheme_name(cls, key: str) -> str:
        """获取配色方案的中文名"""
        return cls._BASE_SCHEMES.get(key, {}).get("name", key)

    @classmethod
    def list_schemes(cls) -> list:
        """列出所有配色方案 [(key, name), ...]"""
        return [(k, v["name"]) for k, v in cls._BASE_SCHEMES.items()]
