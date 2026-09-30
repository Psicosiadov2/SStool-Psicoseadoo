"""
SSTool - punto de entrada.

Requisitos (instalar en tu PC antes de correr o compilar):
    pip install customtkinter pillow

Ejecutar en desarrollo:
    python main.py

Compilar a .exe para Windows:
    BUILD_EXE.bat

El .exe resultante queda en dist/PsicoseadoSSTool.exe. Al abrirlo la primera vez,
la app crea automaticamente la carpeta tools/<categoria>/ al lado del .exe.
"""

def main():
    # Keep imports inside the guard: missing bundled modules must also be logged.
    from core.startup_errors import report_error
    try:
        from core.elevation import ensure_admin
        from core.windows_shell import configure_process_identity
        from ui.app import App
        if ensure_admin():
            configure_process_identity()
            app = App()
            app.report_callback_exception = report_error
            app.mainloop()
        return 0
    except Exception:
        import sys
        report_error(*sys.exc_info())
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
