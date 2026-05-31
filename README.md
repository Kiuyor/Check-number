# Check-number 🎲

基于 PyQt5 的加权概率随机点名器。学生被抽取次数越少，被选中概率越高。支持名单加密、导入导出、悬浮球最小化、7 套配色方案、窗口透明度调节、字体切换。

## 版本

| 版本 | 框架 | 说明 |
|------|------|------|
| **v9.1** | PyQt5 模块化 | 最新版，12 个模块，架构精炼 + 功能增强 |
| v9.0 | PyQt5 模块化 | 9 个模块，代码质量全面优化 |
| v8.0 | PyQt5 单文件 | 577 行，完整 GUI 功能 |
| v5.0.0 | tkinter | 成熟 tkinter 版，三种变体 |

## 快速开始

```bash
pip install PyQt5
python v9.1.py
```

## 功能

| 功能 | 说明 |
|------|------|
| 🎯 加权随机 | 逆频次加权 — 被抽中越少的学生概率越高 |
| 📋 名单导入 | 右键 → 导入名单，选择 .txt 文件（每行一个名字），关闭后不重置 |
| 🔒 名单加密 | XOR 加密存储至 `names.enc`，保护隐私 |
| 🟢 悬浮球 | Esc 最小化到屏幕右侧圆形球，点击恢复 |
| 🎨 配色方案 | 7 套主题（靛蓝/海蓝/翡翠绿/日落橙/玫瑰粉/紫罗兰/晴空蓝） |
| 🔍 窗口透明度 | 5 档预设（30%~90%）+ 滑块实时预览，仅背景半透明文字清晰 |
| 🔤 显示字体 | 4 款字体可选（HarmonyOS Sans / Inter Display / Open Sans / Noto Sans） |
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

## 右键菜单

```
├── 导入名单
├── 统计 ▸ (查看统计信息 / 查看抽取历史 / 清除抽取历史 / 重置数据 / 导出统计数据)
├── 配色方案 ▸ (靛蓝 / 海蓝 / 翡翠绿 / 日落橙 / 玫瑰粉 / 紫罗兰 / 晴空蓝)
├── 窗口透明度 ▸ (极透明 / 高透明 / 默认 / 低透明 / 微透明 / 自定义...)
├── 显示字体 ▸ (HarmonyOS Sans / Inter Display / Open Sans / Noto Sans)
├── 快捷键说明
├── 关于软件
├── 关闭程序
```

## 项目结构

```
├── v9.1.py              # 应用入口
├── config.py            # 配置、路径、偏好、QSS 样式
├── design_tokens.py     # 7 套配色方案 Token
├── main_window.py       # 主窗口（UI + 事件 + 对话框）
├── student_manager.py   # 名单管理（加载/导入/加解密）
├── stats_manager.py     # 统计管理（CRUD/概率计算/导出）
├── history_manager.py   # 历史管理（CRUD）
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
| `config.json` | `文档/check number/` | 用户偏好（配色/透明度/字体/位置） |

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

## 编译与分发

```bash
# Nuitka 编译
pip install PyQt5 nuitka
python -m nuitka --standalone --windows-console-mode=disable --output-dir=build --output-filename=CheckNumber.exe --include-data-files=whs_update=whs_update v9.1.py

# NSIS 打包（需安装 NSIS，编辑 installer.nsi 确保路径正确）
makensis installer.nsi
```

已预构建安装包见 [GitHub Releases](https://github.com/Kiuyor/Check-number/releases)。

## 更新日志

详见 [whs_update](whs_update)

## 许可

MIT License © 2023-2026 Kiuyor

如有建议请联系：750173212@qq.com
