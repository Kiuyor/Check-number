import tkinter as tk
import random
import json

# 创建窗口
window = tk.Tk()
window.title("随机抽学号")
window.geometry("1920x1000+0+0")  # 设置窗口位置为左上角
window.attributes("-alpha", 0.9)
window.overrideredirect(True)
# 读取上一次的统计数据
try:
    with open("statistics.json", "r") as file:
        statistics = json.load(file)
except FileNotFoundError:
    statistics = {}

# 关闭窗口
def close_window():
    # 保存统计数据到文件，并格式化输出
    with open("statistics.json", "w") as file:
        json.dump(statistics, file, indent=4)  # 使用indent参数进行格式化输出
    window.destroy()

close_button = tk.Button(window, text="关闭", command=close_window, activebackground="green", height=2, width=7, font=("Source Han Sans CN", 15), highlightbackground="green", highlightcolor="green")
close_button.pack(side=tk.RIGHT, anchor=tk.E, fill=tk.Y)

# 最小化窗口
def minimize_window():
    window.iconify()  # 最小化窗口

minimize_button = tk.Button(window, text="最小化", command=minimize_window, activebackground="cyan", height=2, width=7, font=("Source Han Sans CN", 15), highlightbackground="cyan", highlightcolor="cyan")
minimize_button.pack(side=tk.LEFT, anchor=tk.W, fill=tk.Y)

# 显示学号的标签
label = tk.Label(window, text="点击按钮开始抽取", font=("Source Han Sans CN", 150))
label.pack(side=tk.TOP, anchor=tk.CENTER)

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

    number = random.choices(list(probabilities.keys()), weights=list(probabilities.values()))[0]

    statistics[number] += 1

    label.config(text=number)

    with open("statistics.json", "w") as file:
        json.dump(statistics, file, indent=4)

# 抽取按钮
button = tk.Button(window, text="抽取", command=draw, height=3, width=10, activebackground="red", font=("Source Han Sans CN", 50), highlightbackground="red", highlightcolor="red")
button.pack(side=tk.BOTTOM)

#绑定键盘事件
window.bind('n', draw) # 当按下'n'键时执行抽取操作
window.bind('p', draw) # 当按下'p'键时执行抽取操作
window.bind('<Prior>', draw) # 当按下'PgUP'键时执行抽取操作
window.bind('<Next>', draw) # 当按下'PgDn'键时执行抽取操作
window.bind('<Left>', draw) # 当按下左光标键时执行抽取操作
window.bind('<Right>', draw) # 当按下右光标键时执行抽取操作

# 进入主循环
window.mainloop()
