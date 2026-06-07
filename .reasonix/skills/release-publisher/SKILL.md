---
name: release-publisher
description: >
  为 Check-number 项目执行完整发布流程：更新版本号、追加更新日志、运行测试、Git 提交/打标签/推送、构建安装包、输出 GitHub Release 上传指引。
  当用户说"发布 vX.Y"、"打新版本"、"发布版本"、"准备发布"等明确版本发布指令时触发。
  不要仅因为用户讨论代码变更就触发——必须是指令式的版本发布请求。
---

# Release Publisher — Check-number 发布流水线

本 skill 将 Check-number 项目的版本发布流程自动化。调用时用户需要提供**新版本号**和**发布内容描述**。

## 输入格式

用户触发时应类似：
- "发布 v9.4 修复了统计窗口排序 bug"
- "打 v10.0 版本，新增分组抽取功能"
- "准备发布 v9.5"

## 工作流（严格按顺序执行）

### 步 1：解析版本信息

从用户指令中提取：
- **版本号**：如 `v9.4` 或 `9.4`（去掉 `v` 前缀作为数字部分，如 `9.4`）
- **版本名称**：发布标题，中文简洁描述（如 "统计窗口修复"、"分组抽取功能"）
- **发布内容详情**：如果有详细日志内容，用户可能通过对话提供；如果未提供，询问用户日志内容后再继续

### 步 2：运行测试套件

在开始任何修改前先确认测试通过：

```bash
python tests/test_core.py
```

如果测试失败，**停下来**报告给用户，不继续发布。

### 步 3：更新 whs_update

`whs_update` 文件在项目根目录，格式为：

```
vX.Y (YYYY-MM-DD) — 版本名称
------------------------------------------
🎯 新功能
  - ...
⚖️ 算法升级
  - ...
🔧 代码改进
  - ...
🐛 修复
  - ...
```

**操作**：
1. 在文件最顶部（标题行 `Check-number 更新日志` 之后）插入新的版本块
2. 日期使用当天日期，格式 `YYYY-MM-DD`
3. 如果用户未提供完整的分类内容，先问用户再填。不要编造内容

### 步 4：更新版本号引用（使用 `scripts/update_release.py`）

运行辅助脚本一次性替换所有文件中的版本号：

```bash
python .reasonix/skills/release-publisher/scripts/update_release.py <旧版本号> <新版本号>
```

例如从 v9.3 升级到 v9.4：

```bash
python .reasonix/skills/release-publisher/scripts/update_release.py 9.3 9.4
```

脚本会自动更新以下文件中的发布版本号：
- `installer.nsi` — VIProductVersion、DisplayVersion、DisplayName

**不会更新**（永远不变，不随发布版本变化）：
- `build.ps1` — Nuitka 输出/构建目录永远为 `v9.2`（与入口脚本 `v9.2.py` 绑定）
- `installer.nsi` 中的注释头 `; CheckNumber v9.2` 和 `File /r "build\v9.2.dist\*"` ——同样绑定 build 目录
- `v9.2.py` — 入口文件名永远不变
- `README.md` — 其中的 v9.2.py 引用是文件名

### 步 5：再次运行测试

更新文件后确认没有破坏任何东西：

```bash
python tests/test_core.py
```

### 步 6：Git 提交 + 打标签 + 推送

```bash
git add -A
git commit -m "vX.Y: 版本名称"
git tag vX.Y
git push origin main --tags
```

### 步 7：构建安装包

```bash
.\build.ps1 -Clean
```

监控输出，确认：
- Nuitka 编译成功
- DPI manifest 嵌入成功
- NSIS 安装包生成成功（`CheckNumber-Setup.exe`）

### 步 8：输出 GitHub Release 上传指引

向用户展示以下内容（用代码块或清晰格式）：

```
## Release 已就绪 ✅

| 项目 | 值 |
|------|-----|
| 版本号 | vX.Y |
| Git 标签 | vX.Y (已推送) |
| 安装包 | CheckNumber-Setup.exe (~27MB) |

请到以下链接创建 GitHub Release：

  https://github.com/Kiuyor/Check-number/releases/new

1. **Tag**: vX.Y（自动选中）
2. **Title**: vX.Y — 版本名称
3. **正文**: 从 whs_update 复制新版本块内容
4. **附件**: 上传桌面 check\CheckNumber-Setup.exe
5. 点击 **Publish release**
```

## 错误处理

- **测试失败**：停止，报告给用户
- **Git 推送失败**：检查网络/权限，提示用户手动推
- **构建失败**：报告构建日志关键行（Nuitka 错误 / NSIS 错误），不继续
- **用户未提供日志分类内容**：发问，不编造

## 原理说明

为什么按这个顺序执行？
- 先测试确保代码健康 → 再改文件 → 再测试确认没改坏 → 再提交 → 再构建。每一步如果前一步失败就停止，防止发布一个有问题或者不完整的版本。
- `update_release.py` 脚本集中管理所有版本号引用，避免人工改 5 个不同位置漏掉其一。
- 手动上传 Release 而非自动（gh CLI），是因为手动可以复审日志内容和附件是否正确。
