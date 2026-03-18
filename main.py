import ctypes
import win32gui
import math
import threading
import tkinter as tk
import time
import os
from winotify import Notification, audio

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw


WM_INPUT = 0x00FF
RID_INPUT = 0x10000003

DPI = 650
SAVE_FILE = "mouse_distance.txt"

total_counts = 0
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def show_notification():
    toast = Notification(
        app_id="Mouse Tracker",
        title="Mouse Tracker",
        msg="Mouse Tracker is still running in the tray",
        duration="short"
    )

    toast.set_audio(audio.Default, loop=False)
    toast.show()


if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        total_counts = float(f.read())


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", ctypes.c_uint),
        ("dwSize", ctypes.c_uint),
        ("hDevice", ctypes.c_void_p),
        ("wParam", ctypes.c_void_p),
    ]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", ctypes.c_ushort),
        ("ulButtons", ctypes.c_ulong),
        ("ulRawButtons", ctypes.c_ulong),
        ("lLastX", ctypes.c_long),
        ("lLastY", ctypes.c_long),
        ("ulExtraInformation", ctypes.c_ulong),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("mouse", RAWMOUSE),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", ctypes.c_ushort),
        ("usUsage", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("hwndTarget", ctypes.c_void_p),
    ]


def wnd_proc(hwnd, msg, wparam, lparam):
    global total_counts

    if msg == WM_INPUT:
        dwSize = ctypes.c_uint(0)

        ctypes.windll.user32.GetRawInputData(
            lparam,
            RID_INPUT,
            None,
            ctypes.byref(dwSize),
            ctypes.sizeof(RAWINPUTHEADER),
        )

        buffer = ctypes.create_string_buffer(dwSize.value)

        ctypes.windll.user32.GetRawInputData(
            lparam,
            RID_INPUT,
            buffer,
            ctypes.byref(dwSize),
            ctypes.sizeof(RAWINPUTHEADER),
        )

        raw = RAWINPUT.from_buffer_copy(buffer)

        dx = raw.mouse.lLastX
        dy = raw.mouse.lLastY

        total_counts += math.sqrt(dx*dx + dy*dy)

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def raw_input_thread():
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = wnd_proc
    wc.lpszClassName = "RawMouse"

    classAtom = win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindow(
        classAtom,
        "RawInput",
        0,
        0, 0, 0, 0,
        0, 0, 0, None
    )

    rid = RAWINPUTDEVICE()
    rid.usUsagePage = 0x01
    rid.usUsage = 0x02
    rid.dwFlags = 0x00000100
    rid.hwndTarget = hwnd

    ctypes.windll.user32.RegisterRawInputDevices(
        ctypes.byref(rid),
        1,
        ctypes.sizeof(rid)
    )

    win32gui.PumpMessages()


def counts_to_meters():
    return (total_counts / DPI) * 0.0254


def update_gui():
    meters = counts_to_meters()
    km = meters / 1000
    label.config(text=f"{meters:.2f} m\n{km:.4f} km")
    root.after(500, update_gui)


def save_loop():
    while True:
        with open(SAVE_FILE, "w") as f:
            f.write(str(total_counts))
        time.sleep(30)

def create_icon():
    return Image.open(resource_path("favicon.ico"))


def show_window(icon, item):
    root.after(0, root.deiconify)


def quit_app(icon, item):
    icon.stop()
    os._exit(0)


def tray_thread():
    icon = pystray.Icon(
        "MouseTracker",
        create_icon(),
        "Mouse Distance Tracker",
        menu=pystray.Menu(
            item("Show Window", show_window),
            item("Quit", quit_app)
        )
    )
    icon.run_detached()
    icon.visible = True


def minimize_to_tray():
    root.withdraw()
    show_notification()



root = tk.Tk()
root.iconbitmap(resource_path("favicon.ico"))
root.protocol("WM_DELETE_WINDOW", minimize_to_tray)
root.title("Mouse Distance Tracker")
root.geometry("300x200")

label = tk.Label(root, text="", font=("Arial", 22))
label.pack(pady=10)


dpi_frame = tk.Frame(root)
dpi_frame.pack(pady=5)
tk.Label(dpi_frame, text="DPI: ").pack(side=tk.LEFT)
dpi_var = tk.StringVar(value=str(DPI))
dpi_entry = tk.Entry(dpi_frame, textvariable=dpi_var, width=6)
dpi_entry.pack(side=tk.LEFT)

def update_dpi():
    global DPI
    try:
        DPI = int(dpi_var.get())
    except ValueError:
        DPI = 650
    dpi_var.set(str(DPI))

tk.Button(root, text="Set DPI", command=update_dpi).pack(pady=5)


threading.Thread(target=raw_input_thread, daemon=True).start()
threading.Thread(target=save_loop, daemon=True).start()
threading.Thread(target=tray_thread, daemon=True).start()

update_gui()
root.mainloop()