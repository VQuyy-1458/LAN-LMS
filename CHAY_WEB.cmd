@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Chua co moi truong Python. Hay chay scripts\setup_windows.ps1 truoc.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\launch_web.py %*
set "launcher_exit=%errorlevel%"
if "%~1"=="" pause
exit /b %launcher_exit%
