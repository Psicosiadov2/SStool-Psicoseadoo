@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo Git no esta instalado. Descargalo de https://git-scm.com/download/win y vuelve a ejecutar.
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
set /p REPO=Pega la URL del repositorio vacio (https://github.com/USUARIO/REPO.git): 
if not exist ".git" git init -b main
git add -A
echo.
echo Archivos que se van a subir:
git ls-files
echo.
echo Revisa la lista. No debe aparecer ningun .exe, dist, build ni .glass-venv.
pause
git commit -m "SSTool+ codigo fuente"
git remote remove origin >nul 2>nul
git remote add origin %REPO%
git branch -M main
git push -u origin main
if errorlevel 1 (
  echo No se pudo subir. Revisa la URL y que el repositorio exista y este vacio.
  pause
  exit /b 1
)
echo Listo: codigo subido a %REPO%
pause
