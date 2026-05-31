import tkinter as tk
from tkinter import ttk
import random
import json
from time import sleep

# 创建窗口
window = tk.Tk()
window.title("随机抽学号")
window.geometry("360x220+0+0")  # 设置窗口大小
window.attributes("-alpha", 1)
window.overrideredirect(True)  # 去掉窗口边框
window.configure(bg='white')  # 设置窗口背景色

# 设置窗口圆角
window.wm_attributes('-alpha', 0.7)  # 设置窗口透明度
window.wm_attributes('-topmost', 1)  # 窗口置顶

# 添加拖动窗口的功能
def start_move(event):
    window.x = event.x
    window.y = event.y

def stop_move(event):
    window.x = None
    window.y = None

def do_move(event):
    dx = event.x - window.x
    dy = event.y - window.y
    x = window.winfo_x() + dx
    y = window.winfo_y() + dy
    window.geometry(f"+{x}+{y}")

window.bind("<ButtonPress-1>", start_move)
window.bind("<ButtonRelease-1>", stop_move)
window.bind("<B1-Motion>", do_move)

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

# 显示学号的标签
label = ttk.Label(window, text="点击", font=("微软雅黑", 80), foreground="black", background='white')
label.pack(side=tk.TOP, anchor=tk.CENTER)

# 抽取按钮
button = ttk.Button(window, text="抽取", command=draw)
button.pack(side=tk.BOTTOM)

# 创建快速模式复选框
check = ttk.Checkbutton(window, text='快速模式', variable=is_fast_mode)
check.pack(side=tk.BOTTOM)

# 关闭按钮
close_button = ttk.Button(window, text="关闭", command=close_window)
close_button.pack(side=tk.RIGHT)

# 进入主循环
window.mainloop()
