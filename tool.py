import threading
import time
import serial
import serial.tools.list_ports
from tkinter import Tk, Button, filedialog, Scale, Checkbutton, IntVar, StringVar, Label, OptionMenu
from PIL import Image, ImageSequence, ImageOps

# ---------- 초기화 ----------
root = Tk()
root.title("GIF to ESP32 OLED")

# 시리얼 포트 선택
def get_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [f"{p.device} - {p.description}" for p in ports]

ports = get_serial_ports()
port_var = StringVar()
port_var.set(ports[0] if ports else "")

Label(root, text="Select COM Port:").pack()
OptionMenu(root, port_var, *ports).pack()

# GIF 옵션 변수
repeat_var = IntVar(value=1)
invert_var = IntVar(value=0)
flip_h_var = IntVar(value=0)
flip_v_var = IntVar(value=0)

Checkbutton(root, text="Repeat", variable=repeat_var).pack()
Checkbutton(root, text="Invert Colors", variable=invert_var).pack()
Checkbutton(root, text="Flip Horizontal", variable=flip_h_var).pack()
Checkbutton(root, text="Flip Vertical", variable=flip_v_var).pack()

# FPS 슬라이더
fps_slider = Scale(root, from_=1, to=100, orient='horizontal', label="Speed")
fps_slider.set(10)  # 기본값 10fps
fps_slider.pack()
fps_label = Label(root, text="Speed: 10")
fps_label.pack()

def update_fps_label(val):
    fps_label.config(text=f"Speed: {val}")
fps_slider.config(command=update_fps_label)

# 현재 상태 표시
status_label = Label(root, text="Status: Idle")
status_label.pack()
current_file_label = Label(root, text="Current File: None")
current_file_label.pack()
current_frame_label = Label(root, text="Current Frame: 0 / 0")
current_frame_label.pack()

# ---------- GIF 전송 ----------
ser = None

def select_gif():
    file_path = filedialog.askopenfilename(filetypes=[("GIF files", "*.gif")])
    if file_path and port_var.get():
        global ser
        port_name = port_var.get().split(" - ")[0]
        if ser:
            ser.close()
        ser = serial.Serial(port_name, 115200, timeout=1)
        threading.Thread(target=send_gif, args=(file_path,), daemon=True).start()

Button(root, text="Select GIF", command=select_gif).pack()

def send_gif(file_path):
    img = Image.open(file_path)
    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    num_frames = len(frames)
    
    current_file_label.config(text=f"Current File: {file_path.split('/')[-1]}")
    
    while repeat_var.get():
        for idx, frame in enumerate(frames):
            current_frame_label.config(text=f"Current Frame: {idx+1} / {num_frames}")
            
            # 변환
            frame_bw = frame.convert('1').resize((128, 64))
            if invert_var.get():
                frame_bw = ImageOps.invert(frame_bw.convert('L')).convert('1')
            if flip_h_var.get():
                frame_bw = ImageOps.mirror(frame_bw)
            if flip_v_var.get():
                frame_bw = ImageOps.flip(frame_bw)
            
            # 1비트 → 1바이트 압축
            img_data = bytearray()
            for y in range(64):
                for x in range(0, 128, 8):
                    byte = 0
                    for bit in range(8):
                        pixel = frame_bw.getpixel((x+bit, y))
                        if pixel == 0:
                            byte |= (1 << (7-bit))
                    img_data.append(byte)
            
            # CHUNK 단위 안정적 전송
            CHUNK = 64
            for i in range(0, len(img_data), CHUNK):
                ser.write(img_data[i:i+CHUNK])
                time.sleep(0.0001)  # 안정성을 위한 딜레이
            
            # FPS → 딜레이 계산
            fps = fps_slider.get()
            delay_s = 1.0 / fps
            time.sleep(delay_s)
            #print(delay_s)
            status_label.config(text="Status: Sending...")

    status_label.config(text="Status: Done")

root.mainloop()
