"""
学生名单管理器 — 负责名单的加载、导入、加解密与持久化。
"""
import os
import random
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

    @staticmethod
    def _encrypt_write(names: list, enc_path: str) -> bool:
        """将名字列表 XOR 加密写入 enc 文件（tmp+replace 原子模式）"""
        try:
            content = "\n".join(names).encode("utf-8")
            encrypted = StudentManager.xor_encrypt_decrypt(content, Config.PASSWORD)
            tmp_path = enc_path + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(encrypted)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, enc_path)
            return True
        except OSError as e:
            print(f"[StudentManager] 名单加密保存失败: {e}", file=sys.stderr)
            return False

    @staticmethod
    def _save_names_to_enc(names: list, enc_path: str) -> bool:
        """将名字列表加密保存到 enc 文件，成功返回 True"""
        return StudentManager._encrypt_write(names, enc_path)

    # ── 默认名单 ──

    # 常见姓氏（百家姓前 80 + 常见复姓）
    _SURNAMES = [
        "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
        "徐", "孙", "马", "胡", "朱", "郭", "何", "罗", "高", "林",
        "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
        "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
        "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎",
        "余", "潘", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜",
        "范", "方", "石", "姚", "谭", "廖", "邹", "熊", "金", "陆",
        "郝", "孔", "白", "崔", "康", "毛", "邱", "秦", "江", "史",
        "欧阳", "上官", "慕容", "夏侯", "司徒", "司马",
    ]

    # 名字常用字（寓意积极）
    _GIVEN_CHARS = [
        "伟", "芳", "娜", "秀", "英", "敏", "静", "丽", "强", "磊",
        "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "兰",
        "霞", "平", "刚", "桂", "文", "华", "飞", "玉", "鑫", "浩",
        "雪", "晨", "博", "辉", "宇", "轩", "泽", "睿", "恒",
        "怡", "萱", "琪", "涵", "彤", "琳", "瑶", "可", "悦", "思",
        "雨", "蕾", "萌", "舒", "月", "宁", "欣", "冰", "璇", "颖",
        "子", "然", "一", "帆", "天", "佑", "嘉", "瑞", "景", "远",
        "鸿", "毅", "安", "逸", "乐", "悠", "信", "诚", "德", "善",
    ]

    @staticmethod
    def _generate_name() -> str:
        """生成一个随机中文姓名"""
        surname = random.choice(StudentManager._SURNAMES)
        # 30% 单名（1字），70% 双名（2字）
        given_len = 1 if random.random() < 0.3 else 2
        given = "".join(random.choices(StudentManager._GIVEN_CHARS, k=given_len))
        return surname + given

    @staticmethod
    def _default_students() -> list:
        """生成随机中文姓名名单（去重，共 NUM_STUDENTS 人）"""
        seen: set = set()
        names: list = []
        while len(names) < Config.NUM_STUDENTS:
            name = StudentManager._generate_name()
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names

    # ── 加载 ──

    def prepare_students_file(self) -> tuple[list, list]:
        """启动时准备学生名单（P2-2: 拆分为三步）。

        Returns:
            (students: list, messages: list[str]) — 学生名单和需要展示的消息列表
        """
        messages = []
        base_dir = Config.get_base_dir()
        os.makedirs(base_dir, exist_ok=True)

        self._upgrade_plaintext(messages)
        return self._load_or_generate(messages)

    def _upgrade_plaintext(self, messages: list):
        """步 1: 若明文文件存在，加密后删除"""
        student_path = Config.get_student_file()
        enc_path = Config.get_enc_file()
        if not os.path.exists(student_path):
            return
        if os.path.exists(enc_path):
            try:
                os.remove(student_path)
                messages.append("检测到名单文件，已保留加密版本")
            except OSError:
                messages.append("名单文件清理失败")
            return
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

    def _load_or_generate(self, messages: list) -> tuple[list, list]:
        """步 2: 加载加密名单，失败/不存在则生成默认"""
        enc_path = Config.get_enc_file()
        if os.path.exists(enc_path):
            names = self._decrypt_in_memory(enc_path)
            if names is not None:
                return names, messages
            messages.append("名单解密失败，已恢复默认")
            return self._default_students(), messages
        messages.append("未找到名单，已生成随机默认名单")
        names = self._default_students()
        if self._save_names_to_enc(names, enc_path):
            messages.append("随机名单已持久化")
        else:
            messages.append("警告：随机名单保存失败，下次启动名单将不一致")
        return names, messages

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
        if not StudentManager._encrypt_write(students, enc_path):
            return None, "名单保存失败", False

        return students, f"名单已加载（共{len(students)}人）", True
