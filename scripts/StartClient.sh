#!/bin/bash
# Mac/Linux için Client başlatma scripti

echo "=========================================="
echo "  Attention Monitor - Client"
echo "=========================================="

cd "$(dirname "$0")"

# Python kontrolü
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "HATA: Python bulunamadı!"
    echo "Python yüklemek için: brew install python3"
    exit 1
fi

echo "Python: $PYTHON"

# Gereksinimleri kontrol et
echo "Gereksinimleri kontrol ediliyor..."
$PYTHON -c "import PyQt5" 2>/dev/null || {
    echo "PyQt5 yükleniyor..."
    pip3 install PyQt5
}

$PYTHON -c "import requests" 2>/dev/null || {
    echo "requests yükleniyor..."
    pip3 install requests
}

echo ""
echo "Client başlatılıyor..."
$PYTHON main.py

