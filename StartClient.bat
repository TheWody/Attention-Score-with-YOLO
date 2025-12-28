@echo off
title Attention Monitor - Teacher Client
color 0B

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║         ATTENTION MONITOR - TEACHER CLIENT                ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.
echo  Uygulama baslatiliyor...
echo.

cd /d "%~dp0"
if exist "dist\AttentionMonitor\AttentionMonitor.exe" (
    start "" "dist\AttentionMonitor\AttentionMonitor.exe"
) else if exist "AttentionMonitor\AttentionMonitor.exe" (
    start "" "AttentionMonitor\AttentionMonitor.exe"
) else (
    echo HATA: AttentionMonitor.exe bulunamadi!
    pause
)

