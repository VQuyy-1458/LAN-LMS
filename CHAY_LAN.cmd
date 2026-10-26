@echo off
setlocal
chcp 65001 >nul
title LAN-LMS - Chay web trong mang LAN
cd /d "%~dp0"
call "%~dp0CHAY_WEB.cmd" --lan %*
set "launcher_exit=%errorlevel%"
echo.
if not "%launcher_exit%"=="0" echo Khong khoi dong duoc. Xem thong bao loi o tren.
echo Nhan phim bat ky de dong cua so nay. Web da chay se tiep tuc chay nen.
pause >nul
exit /b %launcher_exit%
