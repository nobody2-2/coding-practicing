import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import numpy as np
from PIL import Image
import os
import threading
import sys


# 子线程任务
def process_file(callback, file_path):
    image = np.array(Image.open(file_path))

    # 检查图像的形状和数据类型
    print(f"Image shape: {image.shape}")
    print(f"Image dtype: {image.dtype}")

    height = image.shape[0]
    width = image.shape[1]
    alph = image.shape[2]

    #设置更新频率nn
    if(height * width>1000):
        nn=40
    else:
        nn=5

    image_line = np.zeros((height * width, alph))
    matrix_new = np.zeros((height, width)) - 1
    image_processed = image.copy()
    image_line = image.reshape(-1, alph)

    step = np.array([[0, 1], [1, 0], [0, -1], [-1, 0]])
    point = np.array([0, 0])
    o = 0

    total_steps = height * width
    callback('progress_max', total_steps)

    for i in range(total_steps):
        image_processed[point[0]][point[1]] = image_line[i]
        matrix_new[point[0]][point[1]] = 1
        fg = 0
        for j in range(4):
            new_y, new_x = point + step[(o + j) % 4]
            if (0 <= new_x < width) and (0 <= new_y < height) and matrix_new[new_y, new_x] == -1:
                o = (o + j) % 4
                point[:] = new_y, new_x
                fg = True
                break
        if fg == 0:
            break
        
        # 限制调试输出频率，每更新n步输出一次
        if i % nn == 0 or i + 1 == total_steps:
            callback('progress', i + 1)

    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    output_file_path = name + '_process' + ext
    Image.fromarray(image_processed.astype('uint8')).save(output_file_path)

    callback('done', output_file_path)


def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jfif *.jpeg")])
    if file_path:
        text_input.delete(0, tk.END)  # 清空文本框内容
        text_input.insert(0, file_path)  # 显示选择的文件路径
        selected_file_path.set(file_path)  # 保存选择的文件路径


def start_processing():
    file_path = selected_file_path.get()
    if not file_path:
        return

    def callback(msg_type, msg_value):
        if msg_type == 'progress_max':
            progress_bar['maximum'] = msg_value
            print(f'Set max progress: {msg_value}')  # 调试输出
        elif msg_type == 'progress':
            progress_bar['value'] = msg_value
            progress_label.config(text=f'处理进度：{int((msg_value / progress_bar["maximum"]) * 100)}%')
            #print(f'Progress update: {msg_value}')  # 调试输出
            root.update_idletasks()
        elif msg_type == 'done':
            progress_label.config(text="100%")
            print(f'Processing complete: {msg_value}')

            # 重新启用按钮
            select_button.config(state=tk.NORMAL)
            process_button.config(state=tk.NORMAL)

    # 禁用按钮
    select_button.config(state=tk.DISABLED)
    process_button.config(state=tk.DISABLED)

    # 启动一个线程进行处理
    threading.Thread(target=process_file, args=(callback, file_path)).start()


if __name__ == '__main__':

        
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
    # 创建窗口
    root = tk.Tk()
    root.title("图像打乱")
    root.geometry("400x200")

    # 保存选择的文件路径
    selected_file_path = tk.StringVar()

    text_input = tk.Entry(root, width=50)
    text_input.pack()

    select_button = tk.Button(root, text="选择文件", command=select_file)
    select_button.pack()

    process_button = tk.Button(root, text="处理文件", command=start_processing)
    process_button.pack()

    progress_frame = tk.Frame(root)
    progress_frame.pack(pady=10)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
    progress_bar.pack(pady=10)

    progress_label = tk.Label(progress_frame, text="处理进度：0%", anchor="center")
    progress_label.grid(row=0, column=0, sticky="ew")

    status_label = tk.Label(root, text="")
    status_label.pack(pady=5)

    root.mainloop()