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
echo  [!] Bu pencereyi KAPATMAYIN - Sunucu calismaya devam ediyor
echo  [!] Durdurmak icin CTRL+C basin
echo.
echo  ═══════════════════════════════════════════════════════════
echo.

:: Start browser after 2 seconds
start "" "http://localhost:5001/dashboard"

:: Run the server
cd /d "%~dp0"
if exist "dist\AttentionServer\AttentionServer.exe" (
    dist\AttentionServer\AttentionServer.exe
) else if exist "AttentionServer\AttentionServer.exe" (
    AttentionServer\AttentionServer.exe
) else (
    echo HATA: AttentionServer.exe bulunamadi!
    pause
)

pause

