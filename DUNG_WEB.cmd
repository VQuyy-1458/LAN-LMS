@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" exit /b 1
".venv\Scripts\python.exe" scripts\launch_web.py --stop
set "launcher_exit=%errorlevel%"
pause
exit /b %launcher_exit%
