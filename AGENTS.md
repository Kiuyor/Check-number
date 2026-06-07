# Check-number 🎲

基于 PyQt5 的加权概率随机点名器。学生被抽中越少，下一次被选中的概率越高。

## Project

- **语言/框架**: Python 3 + PyQt5
- **入口**: `v9.1.py` (`pip install PyQt5` → `python v9.1.py`)
- **依赖**: 仅 PyQt5（零额外依赖）
- **数据目录**: `%USERPROFILE%\Documents\check number\`（名单加密存储、统计 JSON、历史 JSON、偏好 JSON）

## Commands

| 命令 | 说明 |
|------|------|
| `pip install PyQt5` | 安装依赖 |
| `python v9.1.py` | 运行应用 |
| `.\build.ps1` | 完整构建（Nuitka 编译 + NSIS 安装包） |
| `.\build.ps1 -SkipNuitka` | 仅重新打包 NSIS |
| `.\build.ps1 -SkipInstaller` | 仅 Nuitka 编译 |
| `.\build.ps1 -Clean` | 清理旧构建后完整构建 |
| `makensis installer.nsi` | 直接打包 NSIS 安装包 |

**无测试文件** — 项目没有测试套件。

## Architecture

11 个 Python 模块，统一导入 `config.py` 的 `Config` 类：

| 模块 | 职责 |
|------|------|
| `v9.1.py` | 入口：DPI 适配 → QApplication → 启动画面 → 主窗口 |
| `config.py` | `Config` 类：常量和路径管理、偏好 JSON 读写、QSS 样式生成、共享 JSON 工具 |
| `design_tokens.py` | `DesignTokens` 类：7 套配色方案的 Token 定义与构建（三层合并策略） |
| `main_window.py` | `RandomSelectorWindow` (QMainWindow)：主窗口 UI、事件、动画、右键菜单、对话框 |
| `student_manager.py` | `StudentManager`：名单加载/导入/XOR 加解密、随机默认名单生成 |
| `stats_manager.py` | `StatisticsManager`：统计 CRUD、逆频次概率计算（带缓存）、导出 |
| `history_manager.py` | `HistoryManager`：抽取历史 CRUD |
| `float_ball.py` | `FloatBall`：可拖拽圆形悬浮球迷你窗口 |
| `splash_screen.py` | `SplashScreen`：启动画面（带载入动画） |
| `flash_animation.py` | `FlashAnimation`：名字闪动动画 |
| `sound_manager.py` | `SoundManager`：winsound 蜂鸣音效 |

### 数据流

```
v9.1.py (入口)
  → Config.load_preferences() 加载 config.json
  → SplashScreen 启动画面
  → RandomSelectorWindow
      → StatsManager.load_from_json()  加载 stats.json
      → HistoryManager.load_from_json() 加载 draw_history.json
      → StudentManager.prepare_students_file()  解密 names.enc → 学生名单
      → StatsManager.ensure_initialized()  同步统计键
  → 用户交互: start_draw → FlashAnimation → 结果展示 → 统计/历史写入
```

### 关键设计点

- **概率算法**: 逆频次加权 `p = 1 / (N * (count + 1))`，归一化后 `random.choices()` 抽取。结果缓存于 `_probabilities_cache`，名单变更时失效
- **XOR 加密**: `StudentManager.xor_encrypt_decrypt()` 对称加解密，密钥来自环境变量 `CHECK_NUMBER_KEY` 或内置默认值
- **无线程动画**: `QTimer` + `QPropertyAnimation` 实现闪动和淡入，无需 QThread
- **无边框窗口**: `overrideredirect(True)` + 透明背景 + `-topmost` 置顶，拖拽位置持久化

## Conventions

### 编码风格
- **所有注释和标识符用中文** — 类名/方法名用英文，注释/文档字符串/UI 字符串用中文
- **类方法** — 无状态工具方法都定义为 `@staticmethod` 或 `@classmethod`（如 `StudentManager.xor_encrypt_decrypt`）
- **优先级标注** — 代码中穿插 `P0-1` / `P1-2` / `P2-3` 等优先级标记（P0=最高），修改时注意保留
- **函数签名类型注解** — 返回值类型明确标注（`-> list | None`, `-> bool`）

### 错误处理
- 区分错误类型：`FileNotFoundError` 静默忽略（首次运行），`json.JSONDecodeError` 打印至 stderr 并备份损坏文件，`PermissionError` / `OSError` 打印至 stderr
- 文件写操作使用 `tmp 文件 + os.replace()` 原子替换模式

### UI 模式
- **Toast**: 临时 Toplevel 无边框消息提示（`show_toast()` 方法）
- **主题切换**: `Config.color_scheme` 改变 → `DesignTokens.get(key)` 获取 Token → `Config.get_stylesheet()` 生成 QSS 全文
- **透明度**: 窗口卡片透明（背景半透明，文字不透明）而非窗口整体透明。分两档：窗口卡透明度和悬浮球透明度

### Git / 版本管理
- 忽略 `__pycache__/`, `*.py[cod]`, `build/`, `dist/`, `*.spec`, IDE 目录, `*.enc`, `*.corrupted`
- 更新日志在 `whs_update` 文件

## Notes

（预留，可在此添加后续发现的项目注意事项）
