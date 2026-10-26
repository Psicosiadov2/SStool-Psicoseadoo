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
set /p REPO=URL del repositorio que YA existe (https://github.com/USUARIO/REPO.git): 
set "BR=main"
set /p BR=Rama a actualizar [main]: 
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
rem Alinea el historial con GitHub SIN tocar tus archivos locales.
git reset -q origin/%BR%
if errorlevel 1 (
  echo La rama %BR% no existe en el repositorio.
  pause
  exit /b 1
)
git add -A
echo.
echo Cambios que se van a subir (M=modificado, A=nuevo, D=borrado):
git status --short
echo.
echo Revisa la lista. Si aparece algo con D que NO quieres borrar en GitHub, cierra esta ventana.
pause
git diff --cached --quiet
if not errorlevel 1 (
  echo No hay cambios que subir; GitHub ya esta actualizado.
  pause
  exit /b 0
)
git commit -m "Metodos alternativos de descarga para Eric Zimmerman"
git push origin %BR%
if errorlevel 1 (
  echo No se pudo subir. Si GitHub tiene commits nuevos, ejecuta: git pull --rebase origin %BR% y repite.
  pause
  exit /b 1
)
echo Listo: GitHub actualizado.
pause
