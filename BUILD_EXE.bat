@echo off
call "%~dp0BUILD_GLASS.bat"
exit /b %errorlevel%
setlocal
cd /d "%~dp0"

rem Evita ruedas bloqueadas o con permisos heredados dentro de la cache global.
rem Cada dependencia se descarga limpiamente dentro del entorno de compilacion.
set "PIP_NO_CACHE_DIR=1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

where py >nul 2>nul
if errorlevel 1 (
    echo Python no esta instalado o el comando py no esta disponible.
    echo Instala Python 3.12 x64 con Tcl/Tk y el Python Launcher.
    pause
    exit /b 1
)

py -3.12 -c "import struct; assert struct.calcsize('P') == 8" >nul 2>nul
if errorlevel 1 (
    echo Se requiere Python 3.12 de 64 bits para esta compilacion.
    echo Instala Python 3.12 x64 desde python.org con Tcl/Tk y el Launcher.
    echo No necesitas desinstalar Python 3.13 ni Python 3.14.
    goto :error
)

if not exist ".build-venv-312\Scripts\python.exe" (
    echo Creando entorno de compilacion...
    py -3.12 -m venv .build-venv-312
    if errorlevel 1 goto :error
)

set "BUILD_PY=%CD%\.build-venv-312\Scripts\python.exe"
"%BUILD_PY%" build_support.py --check
if errorlevel 1 goto :error
"%BUILD_PY%" -m pip install --no-cache-dir --upgrade pip
if errorlevel 1 goto :error
"%BUILD_PY%" -m pip install --no-cache-dir -r requirements-build.txt
if errorlevel 1 goto :error
"%BUILD_PY%" -m pip check
if errorlevel 1 goto :error
"%BUILD_PY%" -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo Compilando PsicoseadoSSTool protegido con Nuitka...
"%BUILD_PY%" build_support.py ^
  --mode=onefile ^
  --assume-yes-for-downloads ^
  --enable-plugin=tk-inter ^
  --include-package=customtkinter ^
  --include-package-data=customtkinter ^
  --include-data-files=assets\Intro.png=assets/Intro.png ^
  --include-data-files=assets\PsicoseadoSSTool.png=assets/PsicoseadoSSTool.png ^
  --include-data-files=assets\PsicoseadoSSTool.ico=assets/PsicoseadoSSTool.ico ^
  --windows-console-mode=disable ^
  --windows-uac-admin ^
  --windows-company-name=Psicoseado ^
  --windows-product-name=SSTool+ ^
  --windows-file-description="Psicoseado screenshare toolkit" ^
  --windows-file-version=1.0.0.0 ^
  --windows-product-version=1.0.0.0 ^
  --python-flag=no_docstrings ^
  --python-flag=no_asserts ^
  --lto=yes ^
  --output-dir=dist ^
  --output-filename=SSTool+.exe ^
  --remove-output ^
  main.py
if errorlevel 1 goto :error

echo.
echo Compilacion terminada:
echo "%CD%\dist\SSTool+.exe"
explorer "%CD%\dist"
pause
exit /b 0

:error
echo.
echo La compilacion fallo. Revisa el mensaje mostrado arriba.
pause
exit /b 1
