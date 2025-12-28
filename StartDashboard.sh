#!/bin/bash

echo "=========================================="
echo "  Attention Monitor - Dashboard Server"
echo "=========================================="

cd "$(dirname "$0")"

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

echo "Gereksinimleri kontrol ediliyor..."
$PYTHON -c "import flask" 2>/dev/null || {
    echo "Flask yükleniyor..."
    pip3 install flask flask-sqlalchemy flask-cors
}

echo ""
echo "Dashboard başlatılıyor..."
echo "Tarayıcıda açın: http://localhost:5001/dashboard"
echo ""
echo "Varsayılan Admin:"
echo "  Kullanıcı: admin"
echo "  Şifre: admin123"
echo ""

$PYTHON app_server.py

