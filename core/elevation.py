"""Elevacion UAC de la aplicacion completa en Windows."""

import ctypes
import os
import subprocess
import sys


def is_admin():
    """Indica si el proceso actual ya tiene un token de administrador."""
    if not sys.platform.startswith("win"):
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def _show_uac_error():
    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            "PsicoseadoSSTool necesita permisos de administrador. "
            "Acepta el aviso UAC para poder descargar y abrir las herramientas.",
            "PsicoseadoSSTool",
            0x10,
        )
    except OSError:
        pass


def ensure_admin():
    """Relanza la app con runas y evita continuar sin los permisos requeridos."""
    if not sys.platform.startswith("win") or is_admin():
        return True

    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        executable = sys.executable
        arguments = sys.argv[1:]
        working_directory = os.path.dirname(os.path.abspath(sys.executable))
    else:
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        arguments = [script_path, *sys.argv[1:]]
        working_directory = os.path.dirname(script_path)

    shell_execute = ctypes.windll.shell32.ShellExecuteW
    shell_execute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]
    shell_execute.restype = ctypes.c_void_p
    result = shell_execute(
        None,
        "runas",
        executable,
        subprocess.list2cmdline(arguments) if arguments else None,
        working_directory,
        1,
    )
    if int(result or 0) <= 32:
        _show_uac_error()
    return False
