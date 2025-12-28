@echo off
title Attention Monitor - Admin Dashboard Server
color 0A

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║         ATTENTION MONITOR - ADMIN DASHBOARD               ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

:: Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo  Sunucu baslatiliyor...
echo.
echo  ═══════════════════════════════════════════════════════════
echo.
echo  Dashboard Adresleri:
echo.
echo    Yerel:    http://localhost:5001/dashboard
echo    Ag:       http://%IP%:5001/dashboard
echo.
echo  ═══════════════════════════════════════════════════════════
echo.
echo  Giris Bilgileri:
echo    Kullanici: admin
echo    Sifre:     admin123
echo.
echo  ═══════════════════════════════════════════════════════════
echo.

:: Change to project root directory
cd /d "%~dp0\.."

:: Run the server
python -m server.app

pause

