#导入库
import ctypes
from tkinter.ttk import *

# 导入 tkinter 模块
import tkinter as tk
# 导入 random 模块
import random

# 创建一个窗口对象
window = tk.Tk()

#设置缩放因子
window.tk.call('tk', 'scaling', 96/75)
# 设置窗口标题
window.title("随机抽学号")
# 设置窗口大小
window.geometry("1720x780+100+100")

# 创建一个标签对象，用于显示学号
label = tk.Label(window, text="点击按钮开始抽取", font=("Source Han Sans CN", 60))
# 将标签放置在窗口中央
label.pack()

# 创建一个列表对象，用于存储已经抽过的学号
drawn = []

# 定义一个函数，用于生成随机学号并更新标签内容
def draw():
    # 生成一个 1 到 51 的随机整数
    number = random.randint(1, 51)
    # 检查是否重复
    while number in drawn:
        # 如果重复就重新生成
        number = random.randint(1, 51)
    # 将不重复的学号添加到列表中
    drawn.append(number)
    # 将标签内容设置为随机学号
    label.config(text=str(number))

# 创建一个按钮对象，用于触发抽取函数
button = tk.Button(window, text="再抽一次", command=draw,height = 5, width = 20, font=("Source Han Sans CN", 30))
# 将按钮放置在窗口底部
button.pack(side=tk.BOTTOM)

# 进入主循环，等待用户操作
window.mainloop()
