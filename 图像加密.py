import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import numpy as np
from PIL import Image, UnidentifiedImageError
import os
import threading
import sys


# 子线程任务
def process_file(callback, file_path, mod):

    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    output_file_path = name + '_process' + ext

    try:
        pil_image=Image.open(file_path)
    except FileNotFoundError:
        print(f"文件未找到：{file_path}")
    except UnidentifiedImageError:
        print(f"无法识别的图像文件：{file_path}")
    except Exception as e:
        print(f"发生错误：{str(e)}")
    
    print(f"类型 {ext}")

    if(ext=='.gif'or ext=='.GIF'):
        frame=pil_image.n_frames
        print(f"帧数 {frame}")
    if((ext=='.gif'or ext=='.GIF') and frame>1):
        frames = []
        durations = []
        callback('gif',[0,frame])
        for frame_index in range(frame):
            #检查第一帧是否为索引色
            pil_image.seek(frame_index)
            #检测是否为调色板模式（调色板模式：image.mode=P 在 GIF 中，颜色通常存储在调色板中，并使用索引引用颜色。
            #这种模式叫做 "P" 模式或调色板模式。尽管这种方式节省了存储空间，但在某些情况下，尤其是在使用代码处理图像时，可能会导致显示问题。
            if(pil_image.mode!='P'):
                image = np.array(pil_image)
            else:
                 rgb_image=pil_image.convert("RGB")
                 image = np.array(rgb_image)
            # 检查图像的形状和数据类型
            print(f"第{frame_index}帧\n帧速 {pil_image.info['duration']}ms")
            print(f"分辨率: {image.shape}")
            print(f"图片dtype: {image.dtype}")
            print(f"模式 {pil_image.mode}")
            frames.append(Image.fromarray(code(callback, mod,image,pil_image.mode=='L')))
            durations.append(pil_image.info['duration'])
            callback('gif',[frame_index+1,frame])
        frames[0].save(output_file_path, save_all=True, append_images=frames[1:], loop=0,duration=durations)
    else:
        # 检查图像的形状和数据类型
        image = np.array(pil_image)

        print(f"Image shape: {image.shape}")
        print(f"Image dtype: {image.dtype}")
        print(f"模式 {pil_image.mode}")
        
        image_out=code(callback, mod,image,pil_image.mode=='L')

        Image.fromarray(image_out.astype('uint8')).save(output_file_path)
    os.startfile(output_file_path)

    callback('done', output_file_path)

def code(callback, mod, image,alph_mod):
    height = image.shape[0]
    width = image.shape[1]
    if(alph_mod):
        alph=1
    else:
        alph = image.shape[2]

    image_line = np.zeros((height * width, alph))
    matrix_new = np.zeros((height, width)) - 1
    image_processed = image.copy()
    image_line = image.reshape(-1, alph)

    step = np.array([[0, 1], [1, 0], [0, -1], [-1, 0]])
    point = np.array([0, 0])
    o = 0

    total_steps = height * width
    callback('progress_max', total_steps)
    nn=total_steps//100

    for i in range(total_steps):
        if(mod==1):
            image_processed[point[0]][point[1]] = image_line[i]
        if(mod==2):
            image_processed[i//width][i%width] = image[point[0]][point[1]]
        matrix_new[point[0]][point[1]] = i
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
    return image_processed


def select_file():
    file_sort='''*.bmp;*.BMP;*.eps;*.EPS;*.gif;*.GIF;*.icns;
    *.ICNS;*.ico;*.ICO;*.im;*.IM;*.jpeg;*.JPEG;*.jpg;*.JPG;*.jp2;*.JP2;*.j2k;
    *.J2K;*.jpc;*.JPC;*.jpf;*.JPF;*.jpx;*.JPX;*.msp;*.MSP;*.pcx;*.PCX;*.png;
    *.PNG;*.ppm;*.PPM;*.pbm;*.PBM;*.pgm;*.PGM;*.pnm;*.PNM;*.sgi;*.SGI;*.rgb;
    *.RGB;*.tga;*.TGA;*.tpic;*.TPIC;*.tiff;*.TIFF;*.tif;*.TIF;*.webp;*.WEBP;
    *.xbm;*.XBM;*.xpm;*.XPM'''
    file_path = filedialog.askopenfilename(filetypes=[("Image files",file_sort)])
    if file_path:
        text_input.delete(0, tk.END)  # 清空文本框内容
        text_input.insert(0, file_path)  # 显示选择的文件路径
        selected_file_path.set(file_path)  # 保存选择的文件路径


def start_processing(mod):
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
            progress_bar['value'] =progress_bar['maximum']
            progress_label.config(text="100%")
            print(f'Processing complete: {msg_value}')# 调试输出
            # 重新启用按钮
            select_button.config(state=tk.NORMAL)
            code_button.config(state=tk.NORMAL)
            encode_button.config(state=tk.NORMAL)
            text_outout.insert(tk.END, f'保存为{msg_value}')
        elif msg_type == 'gif':
            gif_label.config(text=f'(处理gif动图)gif帧处理进度：{msg_value[0]}/{msg_value[1]}')
            root.update_idletasks()


    # 禁用按钮
    select_button.config(state=tk.DISABLED)
    code_button.config(state=tk.DISABLED)
    encode_button.config(state=tk.DISABLED)

    # 启动一个线程进行处理
    threading.Thread(target=process_file, args=(callback, file_path, mod)).start()


if __name__ == '__main__':

        
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
    # 创建窗口
    root = tk.Tk()
    root.title("图像打乱")
    root.geometry("400x250")

    #保存选择的文件路径
    selected_file_path = tk.StringVar()

    text_input = tk.Entry(root, width=50)
    text_input.pack(pady=2)

    #按钮
    select_button = tk.Button(root, text="选择文件", command=select_file)
    select_button.pack(pady=2)
    code_button = tk.Button(root, text="加密文件",command= lambda: start_processing(1))
    code_button.pack(pady=2)
    encode_button = tk.Button(root, text="解密文件",command= lambda:  start_processing(2))
    encode_button.pack(pady=2)

    #进度条和进度文字
    progress_frame = tk.Frame(root)
    progress_frame.pack(pady=5)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
    progress_bar.pack(pady=5)

    progress_label = tk.Label(progress_frame, text="处理进度：0%", anchor="center")
    progress_label.grid(row=0, column=0, sticky="ew")

    gif_label = tk.Label(progress_frame, text="(处理gif动图)gif帧处理进度：", anchor="center")
    gif_label.grid(row=1, column=0, sticky="ew")

    #存储文件的文件路径
    text_outout =tk.Text(root,width=50,height=1)
    text_outout.insert(tk.END, f'文件已保存为')
    text_outout.pack(pady=2)

    root.mainloop()