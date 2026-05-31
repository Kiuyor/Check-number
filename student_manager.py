"""
学生名单管理器 — 负责名单的加载、导入、加解密与持久化。
"""
import os
from PyQt5.QtWidgets import QFileDialog
from config import Config


class StudentManager:
    """学生名单管理器 — 文件 I/O + XOR 加解密"""

    def __init__(self):
        pass

    # ── 加解密 ──

    @staticmethod
    def xor_encrypt_decrypt(data: bytes, key: str) -> bytes:
        """XOR 对称加解密（同一函数加解密互通）"""
        key_bytes = key.encode('utf-8')
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

    @staticmethod
    def _decrypt_in_memory(enc_path: str) -> list | None:
        """在内存中解密 enc 文件，返回名字列表（失败返回 None）"""
        try:
            with open(enc_path, "rb") as f:
                encrypted = f.read()
            decrypted = StudentManager.xor_encrypt_decrypt(encrypted, Config.PASSWORD)
            text = decrypted.decode("utf-8")
            names = [line.strip() for line in text.splitlines() if line.strip()]
            return names
        except (OSError, UnicodeDecodeError):
            return None

    # ── 默认名单 ──

    @staticmethod
    def _default_students() -> list:
        """生成默认数字名单 [1, 2, ..., NUM_STUDENTS]"""
        return [str(i) for i in range(1, Config.NUM_STUDENTS + 1)]

    # ── 加载 ──

    def prepare_students_file(self) -> tuple[list, list]:
        """启动时准备学生名单。

        Returns:
            (students: list, messages: list[str]) — 学生名单和需要展示的消息列表
        """
        messages = []
        base_dir = Config.get_base_dir()
        os.makedirs(base_dir, exist_ok=True)
        student_path = Config.get_student_file()
        enc_path = Config.get_enc_file()

        # 步 1: 若明文文件存在，加密后删除
        if os.path.exists(student_path):
            if os.path.exists(enc_path):
                try:
                    os.remove(student_path)
                    messages.append("检测到名单文件，已保留加密版本")
                except OSError:
                    messages.append("名单文件清理失败")
            else:
                try:
                    with open(student_path, "rb") as f:
                        content = f.read()
                    encrypted = self.xor_encrypt_decrypt(content, Config.PASSWORD)
                    tmp_path = enc_path + ".tmp"
                    with open(tmp_path, "wb") as f:
                        f.write(encrypted)
                    os.replace(tmp_path, enc_path)
                    os.remove(student_path)
                    messages.append("已加密名单并删除原文件")
                except OSError:
                    messages.append("名单加密失败")

        # 步 2: 加载加密名单
        if os.path.exists(enc_path):
            names = self._decrypt_in_memory(enc_path)
            if names is not None:
                return names, messages
            else:
                messages.append("名单解密失败，已恢复默认")
                return self._default_students(), messages
        else:
            messages.append("未找到名单，已恢复默认")
            return self._default_students(), messages

    def load_students(self, file_path: str | None) -> tuple[list, str]:
        """从指定文件路径加载学生名单。

        Returns:
            (students: list, message: str)
        """
        if file_path is None:
            return [], "未指定名单路径"
        students = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name:
                        students.append(name)
        except (OSError, UnicodeDecodeError) as e:
            return [], f"名单读取失败: {e}"
        return students, f"名单已加载（共{len(students)}人）"

    def load_students_from_list(self, students: list) -> tuple[list, str]:
        """从列表加载学生名单（空则回退默认）。

        Returns:
            (students: list, message: str)
        """
        if students:
            return students, f"名单已加载（共{len(students)}人）"
        else:
            return self._default_students(), "名单为空，已恢复默认"

    # ── 导入 ──

    def import_student_list(self, parent) -> tuple[list | None, str, bool]:
        """通过文件对话框导入名单，加密保存。

        Args:
            parent: QWidget 父窗口（用于对话框定位和 toast）

        Returns:
            (students: list|None, message: str, should_reset_stats: bool)
            — students 为 None 表示取消/失败，should_reset_stats 表示是否需要重置统计
        """
        path, _ = QFileDialog.getOpenFileName(
            parent, "导入学生名单",
            Config.get_base_dir(),
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if not path:
            return None, "", False

        # 读取文件
        students = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip()
                    if name:
                        students.append(name)
        except (OSError, UnicodeDecodeError) as e:
            return None, f"名单读取失败: {e}", False

        if not students:
            return None, "名单为空，未做更改", False

        # 加密保存
        enc_path = Config.get_enc_file()
        try:
            content = '\n'.join(students).encode('utf-8')
            encrypted = self.xor_encrypt_decrypt(content, Config.PASSWORD)
            with open(enc_path, 'wb') as f:
                f.write(encrypted)
        except OSError as e:
            return None, f"名单保存失败: {e}", False

        return students, f"名单已加载（共{len(students)}人）", True
