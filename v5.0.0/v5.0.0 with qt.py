import sys
import random
import json
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QCheckBox, QGridLayout, QWidget
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor

# 读取上一次的统计数据
try:
    with open("statistics.json", "r") as file:
        statistics = json.load(file)
except FileNotFoundError:
    statistics = {}

class DrawThread(QThread):
    name_signal = pyqtSignal(str)

    def __init__(self, students):
        super().__init__()
        self.students = students

    def run(self):
        for _ in range(70):
            temp_number = random.choice(self.students)
            self.name_signal.emit(temp_number)
            time.sleep(0.025)

class RoundWindow(QMainWindow):
    def __init__(self):
        super(RoundWindow, self).__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # 去掉窗口边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明

        self.setGeometry(300, 300, 300, 200)  # 设置窗口大小

        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.layout = QGridLayout()
        self.label = QLabel("点击抽取", self)
        self.button = QPushButton("抽取", self)
        self.button.clicked.connect(self.draw)
        self.close_button = QPushButton("关闭", self)
        self.close_button.clicked.connect(self.close_window)
        self.fast_mode = QCheckBox("快速模式", self)

        self.layout.addWidget(self.label, 0, 0, 1, 2)  # 放在第一行，跨两列
        self.layout.addWidget(self.button, 1, 0)  # 放在第二行第一列
        self.layout.addWidget(self.fast_mode, 1, 1)  # 放在第二行第二列
        self.layout.addWidget(self.close_button, 2, 0, 1, 2)  # 放在第三行，跨两列

        self.widget.setLayout(self.layout)

        self.oldPos = self.pos()

        self.setStyleSheet("""
            QWidget {
                background-color: lightgray;
               border-radius: 10px;
         }
           QPushButton {
              color: white;
               background-color: blue;
               border-radius: 10px;
                padding: 10px;
               font-size: 16px;
         }
            QLabel {
               font-size: 30px;
              font-family: Arial;
                    }
        """)

    def draw(self):
        students = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50']

        if len(students) == 0:
            return

        if len(statistics) == 0:
            for student in students:
                statistics[student] = 0

        # 计算每个学生的抽取概率
        total_draws = sum(statistics.values())
        probabilities = {student: 1 / (50 * (draw_count + 1)) for student, draw_count in statistics.items()}

        # 如果没有启用快速模式，则闪动名字
        if not self.fast_mode.isChecked():
            self.thread = DrawThread(students)
            self.thread.name_signal.connect(self.update_label)
            self.thread.start()
        else:
            number = random.choices(list(probabilities.keys()), weights=list(probabilities.values()))[0]
            statistics[number] += 1
            self.label.setText(number)

    def update_label(self, name):
        self.label.setText(name)

    def close_window(self):
        # 保存统计数据到文件，并格式化输出
        with open("statistics.json", "w") as file:
            json.dump(statistics, file, indent=4)
        self.close()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = RoundWindow()
    window.show()

    sys.exit(app.exec_())
