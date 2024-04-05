import tkinter as tk
from tkinter import ttk
import random
import json
from ttkbootstrap import Style
from time import sleep

# 创建窗口
window = tk.Tk()
window.title("随机抽学号")
window.geometry("1920x1000+0+0")  # 设置窗口位置为左上角
window.attributes("-alpha", 1)

# 设置ttkbootstrap主题
style = Style('litera')
ttk.Style().theme_use('litera')

# 设置窗口背景
bg_image = tk.PhotoImage(file="image.png")
bg_label = tk.Label(window, image=bg_image)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

# 读取上一次的统计数据
try:
    with open("statistics.json", "r") as file:
        statistics = json.load(file)
except FileNotFoundError:
    statistics = {}

# 添加一个新的全局变量用于标记是否启用快速模式
is_fast_mode = tk.BooleanVar()
is_fast_mode.set(False)  # 默认不启用快速模式

# 生成随机学号并更新标签内容
def draw(event=None):
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
    if not is_fast_mode.get():
        for _ in range(50):
            temp_number = random.choice(students)
            label.config(text=temp_number)
            window.update()
            sleep(0.02)

    number = random.choices(list(probabilities.keys()), weights=list(probabilities.values()))[0]

    statistics[number] += 1

    label.config(text=number)

# 关闭窗口
def close_window():
    # 保存统计数据到文件，并格式化输出
    with open("statistics.json", "w") as file:
        json.dump(statistics, file, indent=4)  
    window.destroy()

# 最小化窗口
def minimize_window():
    window.iconify()  # 最小化窗口

# 显示学号的标签
label = ttk.Label(window, text="点击抽取", style='TLabel', font=("微软雅黑", 120), foreground="black")
label.pack(side=tk.TOP, anchor=tk.CENTER)

ink = ttk.Label(window, text="Maker:Ink.", style='TLabel', font=("微软雅黑", 15), foreground="black")
ink.pack(side=tk.BOTTOM, anchor=tk.E)

# 创建一个新的按钮样式
style.configure('Big.TButton', font=("微软雅黑", 20))

# 抽取按钮
button = ttk.Button(window, text="抽取", command=draw, style='Big.TButton')
button.pack(side=tk.BOTTOM)

# 最小化和关闭按钮
minimize_frame = ttk.Frame(window)
minimize_frame.pack(side=tk.LEFT, fill=tk.Y)

close_frame = ttk.Frame(window)
close_frame.pack(side=tk.RIGHT, fill=tk.Y)

minimize_button = ttk.Button(minimize_frame, text="最小化", command=minimize_window, style='info.TButton')
minimize_button.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

close_button = ttk.Button(close_frame, text="关闭", command=close_window, style='success.TButton')
close_button.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

# 创建快速模式复选框
check = ttk.Checkbutton(window, text='快速模式', variable=is_fast_mode, style='TCheckbutton')
check.pack(side=tk.BOTTOM)

# 绑定键盘事件
window.bind('n', draw)  # 当按下'n'键时执行抽取操作
window.bind('p', draw)  # 当按下'p'键时执行抽取操作
window.bind('<Prior>', draw)  # 当按下'PgUP'键时执行抽取操作
window.bind('<Next>', draw)  # 当按下'PgDn'键时执行抽取操作
window.bind('<Left>', draw)  # 当按下左光标键时执行抽取操作
window.bind('<Right>', draw)  # 当按下右光标键时执行抽取操作

# 进入主循环
window.mainloop()
