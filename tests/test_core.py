"""
核心逻辑单元测试 — 无需 GUI 事件循环。
"""
import os
import sys
import tempfile
import json

# 先将项目根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 必须在任何 PyQt5 导入前创建 QApplication
from PyQt5.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

from config import Config
from student_manager import StudentManager
from stats_manager import StatisticsManager
from design_tokens import DesignTokens


# ═══════════════════════════════════════════════════════════════
# StudentManager — XOR 加解密
# ═══════════════════════════════════════════════════════════════

def test_xor_encrypt_decrypt():
    """XOR 对称加解密：加密再解密应恢复原文"""
    key = "test-key-123"
    original = "Hello, 你好! @#$".encode("utf-8")
    encrypted = StudentManager.xor_encrypt_decrypt(original, key)
    assert encrypted != original, "加密后不应与原文相同"
    decrypted = StudentManager.xor_encrypt_decrypt(encrypted, key)
    assert decrypted == original, f"解密后应恢复原文: {decrypted!r} != {original!r}"


def test_xor_encrypt_decrypt_empty():
    """空数据加解密应返回空"""
    assert StudentManager.xor_encrypt_decrypt(b"", "key") == b""


def test_xor_encrypt_decrypt_different_keys():
    """用不同密钥解密应产生乱码（不回原文）"""
    key1, key2 = "key-a", "key-b"
    original = b"test data"
    encrypted = StudentManager.xor_encrypt_decrypt(original, key1)
    decrypted = StudentManager.xor_encrypt_decrypt(encrypted, key2)
    assert decrypted != original, "不同密钥解密不应恢复原文"


# ═══════════════════════════════════════════════════════════════
# DesignTokens — 颜色工具
# ═══════════════════════════════════════════════════════════════

def test_hex_to_rgb():
    assert DesignTokens._hex_to_rgb("#FF0000") == (255, 0, 0)
    assert DesignTokens._hex_to_rgb("#00FF00") == (0, 255, 0)
    assert DesignTokens._hex_to_rgb("#0000FF") == (0, 0, 255)
    assert DesignTokens._hex_to_rgb("#FFFFFF") == (255, 255, 255)
    assert DesignTokens._hex_to_rgb("#000000") == (0, 0, 0)


def test_hex_to_rgb_invalid():
    """非法输入应抛出 ValueError"""
    cases = ["FF0000", "#FFF", "#GGG000"]
    for case in cases:
        try:
            DesignTokens._hex_to_rgb(case)
            assert False, f"应为 {case!r} 抛出 ValueError"
        except ValueError:
            pass


def test_srgb_to_linear():
    # 边界值
    assert abs(DesignTokens._srgb_to_linear(0.0)) < 1e-10
    assert abs(DesignTokens._srgb_to_linear(1.0) - 1.0) < 0.001
    # 线性区 (c <= 0.04045): c / 12.92
    assert abs(DesignTokens._srgb_to_linear(0.0) - 0.0) < 0.001
    # 非线性区 > 0.04045
    assert DesignTokens._srgb_to_linear(0.5) > 0.04  # 粗略检查


# ═══════════════════════════════════════════════════════════════
# DesignTokens — 方案构建
# ═══════════════════════════════════════════════════════════════

def test_build_scheme_has_required_keys():
    """每个配色方案应包含所有必需 Token"""
    required = {"name", "primary", "primary_hover", "primary_active",
                 "gradient_top", "gradient_bottom", "surface_solid",
                 "surface", "on_primary", "text_primary", "text_secondary",
                 "border", "toast_bg", "toast_fg", "btn_min_bg",
                 "btn_min_fg", "ball_bg", "ball_hover",
                 "table_header", "table_border",
                 "table_gold", "table_silver", "table_bronze",
                 "result_gold", "success", "error",
                 "splash_title_fg", "splash_subtitle_fg", "splash_dots_fg",
                 }
    for key, name in DesignTokens.list_schemes():
        tokens = DesignTokens.get(key)
        missing = required - set(tokens.keys())
        extra = set(tokens.keys()) - required
        assert not missing, f"配色 '{name}'({key}) 缺少 Token: {missing}"
        # 允许有额外键（派生值等），不强制


# ═══════════════════════════════════════════════════════════════
# StatisticsManager — 概率计算
# ═══════════════════════════════════════════════════════════════

def test_probabilities_equal_when_no_history():
    """无历史时，所有学生应有相同概率"""
    mgr = StatisticsManager()
    students = ["张三", "李四", "王五"]
    probs = mgr.calculate_probabilities(students)
    assert abs(sum(probs.values()) - 1.0) < 0.001, "概率和应为 1"
    # 所有概率相等 (1/3 每人)
    expected = 1.0 / 3
    for p in probs.values():
        assert abs(p - expected) < 0.001, f"概率应均为 {expected}: {probs}"


def test_probabilities_weight_by_history():
    """被抽中越多的学生概率越低"""
    mgr = StatisticsManager()
    students = ["张三", "李四", "王五"]
    mgr.stats = {"张三": 5, "李四": 1, "王五": 0}
    probs = mgr.calculate_probabilities(students)
    assert probs["王五"] > probs["李四"], "未被抽中的王五概率应最高"
    assert probs["李四"] > probs["张三"], "抽中1次的李四概率应高于抽中5次的张三"
    assert abs(sum(probs.values()) - 1.0) < 0.001, "概率和应为 1"


def test_probabilities_cache():
    """概率应缓存，名单不变时不重算"""
    mgr = StatisticsManager()
    students = ["张三", "李四"]
    p1 = mgr.calculate_probabilities(students)
    p2 = mgr.calculate_probabilities(students)
    assert p1 is p2, "第二次调用应返回同一缓存对象"


def test_probabilities_cache_invalidated_on_increment():
    """increment() 应使缓存失效"""
    mgr = StatisticsManager()
    students = ["张三", "李四"]
    p1 = mgr.calculate_probabilities(students)
    mgr.increment("张三")
    p2 = mgr.calculate_probabilities(students)
    assert p1 is not p2, "increment 后缓存应重建"
    assert p2["李四"] > p2["张三"], "被 increment 后张三概率应降低"


# ═══════════════════════════════════════════════════════════════
# StatisticsManager — 键同步
# ═══════════════════════════════════════════════════════════════

def test_ensure_initialized_adds_new_students():
    """新学生应被初始化为 0 次"""
    mgr = StatisticsManager()
    mgr.stats = {"张三": 5}
    mgr.ensure_initialized(["张三", "李四", "王五"])
    assert mgr.stats["李四"] == 0
    assert mgr.stats["王五"] == 0
    assert mgr.stats["张三"] == 5  # 保留


def test_ensure_initialized_removes_orphans():
    """不在名单中的学生应从统计中移除"""
    mgr = StatisticsManager()
    mgr.stats = {"张三": 5, "李四": 3, "王五": 1}
    mgr.ensure_initialized(["张三", "王五"])
    assert "李四" not in mgr.stats
    assert "张三" in mgr.stats
    assert "王五" in mgr.stats


# ═══════════════════════════════════════════════════════════════
# StatisticsManager — 文件读写（集成测试）
# ═══════════════════════════════════════════════════════════════

def test_save_and_load_json():
    """保存后再加载应恢复相同数据"""
    mgr = StatisticsManager()
    mgr.stats = {"张三": 5, "李四": 3}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        tmp_path = f.name

    try:
        # 替换 stats 文件路径
        original_getter = Config.get_stats_file
        Config.get_stats_file = lambda: tmp_path
        try:
            mgr.save_to_json()
            mgr2 = StatisticsManager()
            mgr2.load_from_json()
            assert mgr2.stats == {"张三": 5, "李四": 3}
        finally:
            Config.get_stats_file = original_getter
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    # 简易运行：pytest 或直接 python tests/
    test_xor_encrypt_decrypt()
    test_xor_encrypt_decrypt_empty()
    test_xor_encrypt_decrypt_different_keys()
    test_hex_to_rgb()
    test_srgb_to_linear()
    test_build_scheme_has_required_keys()
    test_probabilities_equal_when_no_history()
    test_probabilities_weight_by_history()
    test_probabilities_cache()
    test_probabilities_cache_invalidated_on_increment()
    test_ensure_initialized_adds_new_students()
    test_ensure_initialized_removes_orphans()
    test_save_and_load_json()
    print("所有测试通过 [OK]")
