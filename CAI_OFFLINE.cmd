@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
py -3.12 -m scripts.setup_offline
set "setup_exit=%errorlevel%"
pause
exit /b %setup_exit%
