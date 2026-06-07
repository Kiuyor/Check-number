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

    # 各方案的唯一数据（name, primary, primary_hover, primary_active,
    #                  gradient_top, gradient_bottom, btn_min_bg, table_header, table_border）
    # surface_solid / ball_bg / ball_hover 自动从 primary 派生
    _SCHEME_DATA = {
        "indigo":  ("靛蓝",   "#4F46E5", "#4338CA", "#3730A3", "#5B52F0", "#3B3CC4", "#E0E7FF", "#F5F3FF", "#E0E7FF"),
        "ocean":   ("海蓝",   "#0EA5E9", "#0284C7", "#0369A1", "#38BDF8", "#0284C7", "#E0F2FE", "#F0F9FF", "#BAE6FD"),
        "emerald": ("翡翠绿", "#10B981", "#059669", "#047857", "#34D399", "#059669", "#D1FAE5", "#ECFDF5", "#A7F3D0"),
        "sunset":  ("日落橙", "#F97316", "#EA580C", "#C2410C", "#FB923C", "#EA580C", "#FFF7ED", "#FFF7ED", "#FFEDD5"),
        "rose":    ("玫瑰粉", "#EC4899", "#DB2777", "#BE185D", "#F472B6", "#DB2777", "#FCE7F3", "#FDF2F8", "#FBCFE8"),
        "violet":  ("紫罗兰", "#8B5CF6", "#7C3AED", "#6D28D9", "#A78BFA", "#7C3AED", "#EDE9FE", "#F5F3FF", "#DDD6FE"),
        "sky":     ("晴空蓝", "#2563EB", "#1D4ED8", "#1E40AF", "#3B82F6", "#1D4ED8", "#DBEAFE", "#F0F9FF", "#BFDBFE"),
    }
    _SCHEME_KEYS = ["name", "primary", "primary_hover", "primary_active",
                    "gradient_top", "gradient_bottom", "btn_min_bg", "table_header", "table_border"]

    # sky 浅色主题的覆盖项（覆盖 _DEFAULTS 中默认深色底的值）
    _SKY_OVERRIDES = {
        "surface_solid": "#F0F9FF",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "border": "rgba(0, 0, 0, 0.08)",
        "toast_bg": "rgba(15, 23, 42, 0.92)",
        "result_gold": "#000000",
    }

    # ── 由 _SCHEME_DATA 构建的完整方案字典（惰性初始化） ──
    _BASE_SCHEMES = None

    @classmethod
    def _ensure_schemes(cls):
        """惰性构建 _BASE_SCHEMES：从 _SCHEME_DATA + 自动派生值 + _SKY_OVERRIDES 组装。
        (P2-1: 数据驱动消除方案重复)
        """
        if cls._BASE_SCHEMES is not None:
            return
        cls._BASE_SCHEMES = {}
        for key, vals in cls._SCHEME_DATA.items():
            scheme = dict(zip(cls._SCHEME_KEYS, vals))
            # 自动派生
            scheme["surface_solid"] = scheme["primary"]
            scheme["ball_bg"] = scheme["primary"]
            scheme["ball_hover"] = scheme["primary_hover"]
            # sky 特殊处理
            if key == "sky":
                scheme.update(cls._SKY_OVERRIDES)
            cls._BASE_SCHEMES[key] = scheme

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
        cls._ensure_schemes()
        return cls._build_scheme(cls._BASE_SCHEMES[scheme_key])

    @classmethod
    def get_scheme_name(cls, key: str) -> str:
        """获取配色方案的中文名"""
        cls._ensure_schemes()
        return cls._BASE_SCHEMES.get(key, {}).get("name", key)

    @classmethod
    def get_surface_rgb(cls, scheme_key: str) -> tuple:
        """提取 surface_solid 的 (r, g, b) 元组，用于动态 alpha 构造"""
        cls._ensure_schemes()
        solid = cls._BASE_SCHEMES[scheme_key]["surface_solid"]
        return cls._hex_to_rgb(solid)

    @classmethod
    def list_schemes(cls) -> list:
        """列出所有配色方案 [(key, name), ...]"""
        cls._ensure_schemes()
        return [(k, v["name"]) for k, v in cls._BASE_SCHEMES.items()]
