#!/usr/bin/env python3
"""
update_release.py — 统一替换 Check-number 项目各文件中的版本号引用。

用法：
    python update_release.py <旧版本号> <新版本号>

示例：
    python update_release.py 9.3 9.4   # 从 v9.3 升级到 v9.4

负责的文件（只更新与发布版本号相关的行）：
    - installer.nsi（VIProductVersion、DisplayVersion、DisplayName）

不更新的文件及其原因：
    - build.ps1：Nuitka 输出目录永远为 v9.2（与入口脚本 v9.2.py 绑定）
    - installer.nsi 中的注释头和 File 路径：同样绑定 build 目录，永远 v9.2
    - v9.2.py：入口文件名永远不变
    - README.md：其中的 v9.2.py 引用是文件名
    - whs_update：由 release-publisher skill 的步 3 单独处理
"""
import sys
import re
import os


PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", ".."
))


def update_installer_nsi(old_ver: str, new_ver: str) -> bool:
    """更新 installer.nsi 中的发布版本号引用，保留 build 目录相关的 v9.2 不变"""
    path = os.path.join(PROJECT_ROOT, "installer.nsi")
    if not os.path.exists(path):
        print(f"[SKIP] installer.nsi 不存在: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    changes = []

    # VIProductVersion "X.Y.0.0"
    old_vpv = f'"{old_ver}.0.0"'
    new_vpv = f'"{new_ver}.0.0"'
    if old_vpv in content:
        content = content.replace(old_vpv, new_vpv)
        changes.append(f"VIProductVersion {old_vpv} → {new_vpv}")

    # DisplayVersion "X.Y"  (实际的 NSI 中为 "DisplayVersion" "X.Y")
    old_dv = f'"DisplayVersion" "{old_ver}"'
    new_dv = f'"DisplayVersion" "{new_ver}"'
    if old_dv in content:
        content = content.replace(old_dv, new_dv)
        changes.append(f"DisplayVersion → {new_ver}")

    # DisplayName "CheckNumber vX.Y"
    old_dn = f'CheckNumber v{old_ver}"'
    new_dn = f'CheckNumber v{new_ver}"'
    if old_dn in content:
        content = content.replace(old_dn, new_dn)
        changes.append(f"DisplayName → CheckNumber v{new_ver}")

    if changes:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        for c in changes:
            print(f"  [installer.nsi] {c}")
        return True
    else:
        print("  [installer.nsi] 未找到需替换的项")
        return False


def main():
    if len(sys.argv) != 3:
        print("用法: python update_release.py <旧版本号> <新版本号>")
        print("示例: python update_release.py 9.3 9.4")
        sys.exit(1)

    old_ver = sys.argv[1].lstrip("v")
    new_ver = sys.argv[2].lstrip("v")

    ver_pattern = re.compile(r"^\d+\.\d+$")
    if not ver_pattern.match(old_ver) or not ver_pattern.match(new_ver):
        print(f"错误: 版本号格式不对，期望像 9.3 或 9.4")
        sys.exit(1)

    print(f"=== 更新发布版本号: v{old_ver} → v{new_ver} ===")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"注意: build 目录路径保持 v9.2（与入口脚本绑定，不随发布版本变化）")
    print()

    update_installer_nsi(old_ver, new_ver)

    print()
    print("=== 版本号更新完成 ===")
    print(f"以下文件需单独处理（见 release-publisher skill 工作流）:")
    print(f"  - whs_update: 步 3 追加新版本日志块")
    print(f"  - build.ps1: 保持 v9.2 不变（Nuitka 按入口脚本命名）")


if __name__ == "__main__":
    main()
