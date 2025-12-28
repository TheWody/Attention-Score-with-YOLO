@echo off
echo ========================================
echo  Classroom Attention Monitor - Builder
echo ========================================
echo.

REM PyInstaller ile exe oluştur
echo Building exe... (Bu islem 5-10 dakika surebilir)
echo.

pyinstaller --name "AttentionMonitor" ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --add-data "yolov8n-pose.pt;." ^
    --add-data "yolov8n-cls.pt;." ^
    --add-data "server/templates;server/templates" ^
    --hidden-import ultralytics ^
    --hidden-import ultralytics.nn.tasks ^
    --hidden-import cv2 ^
    --hidden-import scipy.stats ^
    --hidden-import matplotlib.pyplot ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    --collect-all ultralytics ^
    main.py

echo.
if exist "dist\AttentionMonitor\AttentionMonitor.exe" (
    echo ========================================
    echo  BUILD BASARILI!
    echo ========================================
    echo.
    echo Exe dosyasi: dist\AttentionMonitor\AttentionMonitor.exe
    echo.
    echo Klasoru tasiyarak dagitabilirsiniz.
) else (
    echo ========================================
    echo  BUILD HATASI!
    echo ========================================
    echo Lütfen hatalari kontrol edin.
)

pause

