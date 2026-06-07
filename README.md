# Check-number 🎲

**加权概率随机点名器** — 学生被抽取次数越少，被选中的概率越高。基于 PyQt5，无边框半透明窗口，支持名单加密、配色切换、悬浮球最小化。

## 快速开始

```bash
pip install PyQt5
python v9.2.py
```

## 功能一览

| 功能 | 说明 |
|------|------|
| 🎯 加权随机 | 逆频次加权 — 被抽中越少概率越高 |
| 📋 名单导入 | 右键 → 导入名单，选择 `.txt` 文件（每行一个姓名） |
| 🔒 XOR 加密 | 名单以 `names.enc` 加密存储，密钥来自 `CHECK_NUMBER_KEY` 环境变量 |
| 🟢 悬浮球 | `Esc` 最小化到屏幕右侧可拖拽白色半透明圆球，点击恢复 |
| 🎨 7 套配色 | 靛蓝 / 海蓝 / 翡翠绿 / 日落橙 / 玫瑰粉 / 紫罗兰 / 晴空蓝 |
| 🔍 窗口透明度 | 5 档预设（30%~90%）+ 滑块实时自定义预览 |
| 🔤 字体切换 | 4 款：HarmonyOS Sans / Inter Display / Open Sans / Noto Sans |
| ⚡ 快速模式 | 右下角按钮，跳过名字闪动动画直接出结果 |
| 🔔 音效 | `winsound.Beep` 合成蜂鸣音效（Windows） |
| 📊 统计弹窗 | 可排序表格，前三名金银铜高亮，支持导出/重置 |
| 📜 历史记录 | 自动记录每次抽取时间、模式、结果，支持清除 |
| 🖱️ 窗口拖拽 | 无边框窗口任意拖拽，关闭时自动记忆位置 |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Space` / `Enter` | 抽取 |
| `Esc` | 最小化到悬浮球 |
| `Ctrl+T` | 循环切换配色方案 |
| 双击 / 右键 | 抽取 / 打开菜单 |

## 右键菜单

```
├── 导入名单
├── 统计 ▸ (查看统计信息 / 查看抽取历史 / 清除抽取历史 / 重置数据 / 导出统计数据)
├── 配色方案 ▸ (靛蓝 / 海蓝 / 翡翠绿 / 日落橙 / 玫瑰粉 / 紫罗兰 / 晴空蓝)
├── 窗口透明度 ▸ (极透明30% / 高透明45% / 默认60% / 低透明75% / 微透明90% / 自定义...)
├── 显示字体 ▸ (HarmonyOS Sans / Inter Display / Open Sans / Noto Sans)
├── 小球透明度 ▸ (微透明30% / 高透明50% / 默认70% / 低透明85% / 实心100% / 自定义...)
├── 快捷键说明
├── 关于软件
└── 关闭程序
```

## 项目结构

```
├── v9.2.py              # 应用入口（DPI 适配 → 启动画面 → 主窗口）
├── config.py            # 常量、路径管理、偏好 JSON 读写、QSS 样式生成
├── design_tokens.py     # 7 套配色方案的 Token 定义（三层合并策略）
├── main_window.py       # 主窗口：UI、事件、动画、右键菜单、对话框
├── student_manager.py   # 名单加载/导入/XOR 加解密、随机默认名单生成
├── stats_manager.py     # 统计 CRUD、逆频次概率计算（带缓存）、导出
├── history_manager.py   # 抽取历史 CRUD（自动截断至 500 条）
├── float_ball.py        # 可拖拽圆形悬浮球迷你窗口
├── splash_screen.py     # 启动画面（圆角卡片 + 点动画 + 淡入淡出）
├── flash_animation.py   # 名字闪动动画（QTimer 递归，无线程）
├── sound_manager.py     # winsound 蜂鸣音效（上升/下降音符序列）
├── students_example.txt # 示例名单（40 人）
├── build.ps1            # 一键构建脚本（Nuitka + NSIS）
├── installer.nsi        # NSIS 安装包脚本
└── AGENTS.md            # AI 辅助开发指南
```

## 数据存储

| 文件 | 路径（Windows） | 说明 |
|------|-----------------|------|
| `names.enc` | `%USERPROFILE%\Documents\check number\` | XOR 加密的学生名单 |
| `stats.json` | `%USERPROFILE%\Documents\check number\stats\` | 每人抽取次数统计 |
| `draw_history.json` | `%USERPROFILE%\Documents\check number\stats\` | 抽取历史记录 |
| `config.json` | `%USERPROFILE%\Documents\check number\` | 用户偏好（配色/透明度/字体/位置） |

## 名单格式

纯文本，每行一个姓名，UTF-8 编码：

```
张三
李四
王五
```

右键 → 导入名单，选择文件即可替换。首次运行无名单时自动生成随机中文姓名（共 60 人）。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CHECK_NUMBER_KEY` | XOR 加密密钥 | 内置默认值 |

## 构建与分发

```bash
# Nuitka 编译
pip install nuitka
python -m nuitka --standalone --enable-plugin=pyqt5 --windows-console-mode=disable --output-dir=build --output-filename=CheckNumber.exe --include-data-files=whs_update=whs_update --assume-yes-for-downloads v9.2.py

# 或使用一键脚本
.\build.ps1              # Nuitka + NSIS 完整构建
.\build.ps1 -SkipNuitka  # 仅重新打包安装包
.\build.ps1 -SkipInstaller  # 仅编译
.\build.ps1 -Clean       # 清理后构建
```

已预构建安装包见 [GitHub Releases](https://github.com/Kiuyor/Check-number/releases)。

## 技术要点

- **概率算法**: 逆频次加权 `p = 1 / (N × (count + 1))`，归一化 + `random.choices()` 抽取，结果缓存
- **名单加密**: `StudentManager.xor_encrypt_decrypt()` 对称加解密，写入时原子替换（tmp → replace）
- **动画**: `QPropertyAnimation`（淡入）+ `QTimer` 递归（闪动），全程无需线程
- **窗口**: `FramelessWindowHint` + `WA_TranslucentBackground`，背景半透明而文字清晰
- **实时预览**: 透明度/字体切换支持 `save=False` 参数，滑块拖动时不写磁盘

## 更新日志

详见 [whs_update](whs_update)

## 许可

MIT License © 2023-2026 Kiuyor | 联系：750173212@qq.com
