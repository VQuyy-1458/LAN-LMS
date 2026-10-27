@echo off
setlocal
chcp 65001 >nul
title LAN-LMS - Cai dat va chay
set "bootstrap=%~dp0scripts\bootstrap_windows.ps1"
if exist "%~dp0LAN-LMS\scripts\bootstrap_windows.ps1" set "bootstrap=%~dp0LAN-LMS\scripts\bootstrap_windows.ps1"
if not exist "%bootstrap%" (
 echo Khong tim thay bo cai. Hay giai nen TOAN BO file ZIP vao o cung truoc.
 pause
 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%bootstrap%" %*
set "result=%errorlevel%"
if not "%result%"=="0" echo Chua hoan tat. Xem thong bao va log trong .runtime\bootstrap\logs.
pause
exit /b %result%
