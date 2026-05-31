# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A random student name picker (点名器) with weighted probability based on past draw counts. Students who have been drawn fewer times get higher probability.

Two versions available:

| 版本 | UI 框架 | 文件 | 启动速度 | 依赖 |
|------|---------|------|---------|------|
| v8.0 | PyQt5 | `v8.0.py` (~597行) | ~320ms | `pip install PyQt5` |
| **v9.0** | **tkinter** | **`v9.0.py`** (~470行) | **~180ms** | **Python 内置，零依赖** |

## Running the app

```
# 推荐：tkinter 轻量版（启动更快）
python v9.0.py

# PyQt5 原版
python v8.0.py
```

## Architecture (v9.0 — tkinter 版本)

单文件 `v9.0.py`。关键类：

- **`Config`** — 常量、路径管理（懒加载缓存）、跨平台字体检测。学生名单 XOR 加密，统计数据以 JSON 存储于 `stats/stats.json`。

- **`RandomSelectorApp`** — 主应用类，包含所有 UI 和业务逻辑：
  - 窗口：`overrideredirect(True)` 无边框 + `attributes('-alpha', 0.92)` 半透明 + `-topmost` 置顶
  - 动画：`after()` 递归调度实现名字闪动（40 步）和结果淡入（35 帧颜色渐变），**无需线程**
  - `_load_stats()` / `_save_stats()` — JSON 统计数据读写
  - `prepare_students_file()` — 启动时加密明文 `student.txt`，从 `names.enc` 解密加载
  - `start_draw()` → `_animate_flash()` → `_perform_draw()` → `_animate_fade_in()` — 抽取流水线
  - `calculate_probabilities()` — 逆频次加权（缓存于 `_probabilities_cache`）
  - `_minimize_to_ball()` / `_restore_from_ball()` — 最小化到屏幕右侧圆形悬浮球
  - `_show_context_menu()` — 右键菜单（tk.Menu），含统计/设置子菜单
  - `_show_statistics()` — ttk.Treeview 表格弹窗（替代原 HTML QTextBrowser）
  - `_show_toast()` — 临时消息提示（Toplevel 无边框窗口）
  - `xor_encrypt_decrypt()` — 对称异或加解密

### 与原 PyQt5 版本的关键差异

| 特性 | v8.0 (PyQt5) | v9.0 (tkinter) |
|------|-------------|----------------|
| 动画线程 | `QThread` + `pyqtSignal` | `root.after()` 递归（主线程） |
| 淡入效果 | `QGraphicsOpacityEffect` (opacity) | Label fg 颜色从背景渐变到金色 |
| 统计弹窗 | `QTextBrowser` + HTML 表格 | `ttk.Treeview` 表格 |
| 窗口透明 | `WA_TranslucentBackground` | `attributes('-alpha', 0.92)` |

## Data flow

1. 启动：`_load_stats()` → `prepare_students_file()` 解密 `names.enc` → `load_students()` → `ensure_statistics_initialized()` 同步统计
2. 抽取：计算逆频次概率 → `random.choices()` → 更新 `self.stats` → `_save_stats()` → 动画展示结果
3. 名单持久化 XOR 加密；统计为明文 JSON
