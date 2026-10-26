@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo Git no esta instalado. Descargalo de https://git-scm.com/download/win
  pause
  exit /b 1
)
for /f "delims=" %%A in ('git config --global user.name 2^>nul') do set "GN=%%A"
if not defined GN (
  set /p GN=Tu nombre para los commits: 
  git config --global user.name "%GN%"
  set /p GE=Tu correo de GitHub: 
  git config --global user.email "%GE%"
)
echo.
echo Este script deja GitHub IDENTICO a esta carpeta:
echo  - sube lo nuevo y lo modificado
echo  - borra de GitHub lo que no exista aqui
echo  - quita lo que este en .gitignore (.exe, dist, build, .glass-venv...)
echo El historial anterior se conserva (no usa force push).
echo.
set /p REPO=URL del repositorio (https://github.com/USUARIO/REPO.git): 
set "BR=main"
set /p BR=Rama [main]: 
if not defined BR set "BR=main"

if not exist ".git" git init -q
git remote remove origin >nul 2>nul
git remote add origin %REPO%
git fetch origin
if errorlevel 1 (
  echo No se pudo leer el repositorio. Revisa la URL y tu inicio de sesion.
  pause
  exit /b 1
)
git symbolic-ref HEAD refs/heads/%BR%
git reset -q origin/%BR%
if errorlevel 1 (
  echo La rama %BR% no existe en el repositorio.
  pause
  exit /b 1
)
git rm -r -q --cached . >nul 2>nul
git add -A
echo.
echo Cambios (A=nuevo, M=modificado, D=se borra de GitHub):
git status --short
echo.
echo Si todo es correcto pulsa una tecla; si no, cierra esta ventana.
pause
git diff --cached --quiet
if not errorlevel 1 (
  echo GitHub ya es identico a esta carpeta. Nada que subir.
  pause
  exit /b 0
)
git commit -m "Sobreescribe el codigo fuente con la version actual"
git push origin %BR%
if errorlevel 1 (
  echo No se pudo subir. Prueba: git pull --rebase origin %BR%  y repite.
  pause
  exit /b 1
)
echo Listo: GitHub ahora es identico a esta carpeta.
pause
