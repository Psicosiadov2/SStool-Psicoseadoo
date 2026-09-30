"""Validate the Windows build runtime and pass real Tcl/Tk paths to Nuitka."""
import struct
import subprocess
import sys
from pathlib import Path


def discover_tk():
    import tkinter

    root = tkinter.Tk()
    root.withdraw()
    try:
        tcl = Path(root.tk.eval('info library'))
        tk = Path(root.tk.eval('set tk_library'))
    finally:
        root.destroy()
    for directory, filename in ((tcl, 'init.tcl'), (tk, 'tk.tcl')):
        if not (directory / filename).is_file():
            raise RuntimeError(f'No se encuentra {directory / filename}')
    return tcl, tk


def main():
    try:
        if sys.platform != 'win32' or sys.version_info[:2] != (3, 12):
            raise RuntimeError('Usa Python 3.12 para Windows.')
        if struct.calcsize('P') != 8:
            raise RuntimeError('Usa Python de 64 bits.')
        tcl, tk = discover_tk()
    except Exception as exc:
        print(f'Error de preparacion: {exc}', file=sys.stderr)
        print('Repara Python 3.12 desde su instalador y habilita Tcl/Tk.', file=sys.stderr)
        return 1
    print(f'Tcl: {tcl}\nTk: {tk}', flush=True)
    if sys.argv[1:] == ['--check']:
        return 0
    return subprocess.call([
        sys.executable, '-m', 'nuitka',
        f'--tcl-library-dir={tcl}', f'--tk-library-dir={tk}',
        *sys.argv[1:],
    ])


if __name__ == '__main__':
    sys.exit(main())
