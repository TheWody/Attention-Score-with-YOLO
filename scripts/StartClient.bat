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

:: Change to project root directory
cd /d "%~dp0\.."

:: Run the client
python main.py

pause

