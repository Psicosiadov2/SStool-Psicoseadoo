"""Integracion visual de PsicoseadoSSTool con el shell de Windows."""

import ctypes
import os
import sys
import tkinter as tk

from core.config import APP_USER_MODEL_ID


GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
SW_MINIMIZE = 6


def configure_process_identity():
    """Asigna identidad estable para el icono y agrupacion en la taskbar."""
    if not sys.platform.startswith("win"):
        return
    try:
        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        set_app_id(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        pass


def force_taskbar_window(window):
    """Hace visible en la taskbar una ventana con barra personalizada."""
    if not sys.platform.startswith("win"):
        return
    try:
        window.update_idletasks()
        user32 = ctypes.windll.user32
        get_parent = user32.GetParent
        get_parent.argtypes = [ctypes.c_void_p]
        get_parent.restype = ctypes.c_void_p
        get_window_long = user32.GetWindowLongW
        get_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
        get_window_long.restype = ctypes.c_long
        set_window_long = user32.SetWindowLongW
        set_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        set_window_long.restype = ctypes.c_long
        set_window_pos = user32.SetWindowPos
        set_window_pos.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        set_window_pos.restype = ctypes.c_bool

        native_id = window.winfo_id()
        handle = get_parent(native_id) or native_id
        style = get_window_long(handle, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        set_window_long(handle, GWL_EXSTYLE, style)
        set_window_pos(
            handle,
            0,
            0,
            0,
            0,
            0,
            SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )
    except (AttributeError, OSError):
        pass


def minimize_taskbar_window(window):
    """Minimiza el HWND real mediante Windows, sin crear el icono antiguo de Tk."""
    if not sys.platform.startswith("win"):
        return False
    try:
        window.update_idletasks()
        force_taskbar_window(window)

        user32 = ctypes.windll.user32
        get_parent = user32.GetParent
        get_parent.argtypes = [ctypes.c_void_p]
        get_parent.restype = ctypes.c_void_p
        show_window = user32.ShowWindow
        show_window.argtypes = [ctypes.c_void_p, ctypes.c_int]
        show_window.restype = ctypes.c_bool

        native_id = window.winfo_id()
        handle = get_parent(native_id) or native_id
        show_window(handle, SW_MINIMIZE)
        return True
    except (AttributeError, OSError, tk.TclError):
        return False


def asset_path(filename):
    """Devuelve la ruta de un asset en codigo fuente, PyInstaller o Nuitka."""
    pyinstaller_root = getattr(sys, "_MEIPASS", None)
    root = pyinstaller_root or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(root, "assets", filename)
