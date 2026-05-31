import tkinter as tk
from tkinter.ttk import *
import random

# 创建窗口
window = tk.Tk()
window.overrideredirect(True)
window.tk.call('tk', 'scaling', 96/75)
window.title("随机抽学号")
window.geometry("1920x1080")
window.attributes("-alpha", 0.9)

# 关闭窗口
def close_window():
    window.destroy()

close_button = tk.Button(window, text="关闭", command=close_window, activebackground="green", height=2, width=7, font=("Source Han Sans CN", 30))
close_button.pack(side=tk.RIGHT, anchor=tk.E, fill=tk.Y)

# 显示学号的标签
label = tk.Label(window, text="点击按钮开始抽取", font=("Source Han Sans CN", 150))
label.pack(side=tk.TOP, anchor=tk.CENTER)

# 已抽过的学号列表
drawn = []
students = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50']

# 生成随机学号并更新标签内容
def draw():
    if len(drawn) == len(students):
        label.config(text="已抽完")
    else:
        number = random.choice(students)
        
        while number in drawn:
            number = random.choice(students)
        
        drawn.append(number)
        label.config(text=str(number))

# 抽取按钮
button = tk.Button(window, text="再抽一次", command=draw, height=3, width=10, activebackground="red", font=("Source Han Sans CN", 50))
button.pack(side=tk.BOTTOM)

# 进入主循环
window.mainloop()

