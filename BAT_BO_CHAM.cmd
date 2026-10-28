@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Chua co Python venv. Chay setup_windows.ps1 truoc.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\prepare_judge.py
set "judge_exit=%errorlevel%"
pause
exit /b %judge_exit%
