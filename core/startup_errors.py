"""Visible diagnostics even in a console-free Windows executable."""
import os
import sys
import tempfile
import traceback
from pathlib import Path


def report_error(exc_type, exc_value, exc_traceback):
    details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    saved_path = None
    for base in (os.environ.get('LOCALAPPDATA'), tempfile.gettempdir()):
        if not base:
            continue
        try:
            path = Path(base) / 'PsicoseadoSSTool' / 'startup-error.log'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(details, encoding='utf-8')
            saved_path = path
            break
        except OSError:
            continue
    message = f'PsicoseadoSSTool encountered an error:\n{exc_value}'
    if saved_path:
        message += f'\n\nError log / Registro de error:\n{saved_path}'
    if sys.stderr is not None:
        print(details, file=sys.stderr)
    if sys.platform.startswith('win'):
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, 'PsicoseadoSSTool', 0x10)
