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
window.geometry("190x98")
window.attributes("-alpha", 0.8)
window.overrideredirect(True)
# 创建一个可置顶按钮的按钮
topmost_button = tk.Button(window, text="置顶", command=lambda: window.attributes("-topmost", 1), height=2, width=2, font=("Source Han Sans CN", 3))
topless_button = tk.Button(window, text="置顶", command=lambda: window.attributes("-topmost", 0), height=3, width=3, font=("Source Han Sans CN", 3))
# 将按钮放置在窗口右上角
topmost_button.pack(side=tk.TOP, anchor=tk.E)
topless_button.pack(side=tk.BOTTOM, anchor=tk.E)

# 创建一个标签对象，用于显示学号
label = tk.Label(window, text="点击抽取", font=("Source Han Sans CN", 30))
# 将标签放置在窗口中央
label.pack()

# 创建一个列表对象，用于存储已经抽过的学号
drawn = []

# 定义一个函数，用于生成随机学号并更新标签内容
def draw():
    # 生成随机名字
    number = random.choice(['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50'])
    # 检查是否重复
    while number in drawn:
        # 如果重复就重新生成
        number = random.choice(['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50'])
    # 将不重复的学号添加到列表中
    drawn.append(number)
    # 将标签内容设置为随机学号
    label.config(text=str(number))

# 创建一个按钮对象，用于触发抽取函数
button = tk.Button(window, text="再抽一次", command=draw,height = 1, width = 5, font=("Source Han Sans CN", 5))
# 将按钮放置在窗口底部
button.pack(side=tk.BOTTOM)


# 进入主循环，等待用户操作
window.mainloop()
