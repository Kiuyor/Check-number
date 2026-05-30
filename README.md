# Check-number 🎲

基于 PyQt5 的加权概率随机点名器。学生被抽取次数越少，被选中概率越高。支持名单加密、导入导出、悬浮球最小化、6 套配色方案。

## 版本

| 版本 | 框架 | 说明 |
|------|------|------|
| **v9.0** | PyQt5 模块化 | 最新版，9 个模块，代码质量全面优化 |
| v8.0 | PyQt5 单文件 | 577 行，完整 GUI 功能 |
| v5.0.0 | tkinter | 成熟 tkinter 版，三种变体 |
| v4.5.0 | tkinter | UI 优化版 |
| v3.0.0 | tkinter | 首个正式版 |

## 快速开始

```bash
pip install PyQt5
python v9.0/v9.0.py
```

## 功能

| 功能 | 说明 |
|------|------|
| 🎯 加权随机 | 逆频次加权 — 被抽中越少的学生概率越高 |
| 📋 名单导入 | 右键 → 导入名单，选择 .txt 文件（每行一个名字），关闭后不重置 |
| 🔒 名单加密 | XOR 加密存储至 `names.enc`，保护隐私 |
| 🟢 悬浮球 | Esc 最小化到屏幕右侧圆形球，点击恢复 |
| 🎨 配色方案 | 6 套主题（靛蓝/海蓝/翡翠绿/日落橙/玫瑰粉/紫罗兰/晴空蓝） |
| ⚡ 快速模式 | 右下角按钮，跳过动画直接出结果 |
| 🔔 音效 | winsound 蜂鸣合成音效（Windows） |
| 📊 统计 | 查看/导出/重置抽取数据，前三名金银铜高亮 |
| 📜 历史 | 自动记录每次抽取时间、模式、结果 |
| 🖱️ 拖拽 | 无边框窗口任意拖拽，位置自动记忆 |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Space` / `Enter` | 抽取 |
| `Esc` | 最小化到悬浮球 |
| `Ctrl+T` | 切换配色方案 |
| 双击 / 右键 | 抽取 / 菜单 |

## 项目结构

```
v9.0/
├── v9.0.py              # 应用入口
├── config.py            # 配置、路径、偏好、QSS 样式
├── design_tokens.py     # 6 套配色方案 Token
├── main_window.py       # 主窗口（UI + 业务逻辑）
├── float_ball.py        # 可拖拽圆形悬浮球
├── splash_screen.py     # 启动画面
├── flash_animation.py   # 名字闪动动画
├── sound_manager.py     # winsound 音效
└── students_example.txt # 示例名单（40 人）
```

## 数据存储

| 文件 | 路径 | 说明 |
|------|------|------|
| `names.enc` | `文档/check number/` | XOR 加密名单 |
| `stats.json` | `文档/check number/stats/` | 抽取统计（明文 JSON） |
| `draw_history.json` | `文档/check number/stats/` | 抽取历史 |
| `config.json` | `文档/check number/` | 用户偏好 |

## 名单格式

纯文本，每行一个姓名，UTF-8 编码：

```
张三
李四
王五
```

右键 → 导入名单，选择文件即可替换。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CHECK_NUMBER_KEY` | XOR 加密密钥 | 内置默认值 |

## 编译

```bash
pip install PyQt5 nuitka
python -m nuitka --standalone --windows-disable-console v9.0/v9.0.py
```

## 更新日志

详见 [whs_update](whs_update)

## 许可

MIT License © 2023-2026 Kiuyor

如有建议请联系：750173212@qq.com
