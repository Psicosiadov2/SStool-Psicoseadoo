@echo off
setlocal
cd /d "%~dp0"
set "PIP_NO_CACHE_DIR=1"
py -3.12 -m venv .glass-venv
if errorlevel 1 goto :error
set "BUILD_PY=%CD%\.glass-venv\Scripts\python.exe"
"%BUILD_PY%" -m pip install --no-cache-dir -r requirements.txt "pyinstaller>=6,<7" pythonnet
if errorlevel 1 goto :error
"%BUILD_PY%" -m unittest discover -s tests -v
if errorlevel 1 goto :error
"%BUILD_PY%" -c "import webview, clr; import webview.platforms.winforms"
if errorlevel 1 goto :error
"%BUILD_PY%" -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin --name SSTool+ --icon NONE --add-data "assets;assets" --collect-all webview --collect-all clr_loader --collect-all pythonnet --hidden-import webview.platforms.winforms --hidden-import webview.platforms.edgechromium --hidden-import clr main.py
if errorlevel 1 goto :error
echo Listo: dist\SSTool+.exe
echo Windows requiere Microsoft Edge WebView2 Runtime.
pause
exit /b 0
:error
echo No se pudo compilar. Revisa el error anterior. Usa Python 3.12 x64.
pause
exit /b 1
