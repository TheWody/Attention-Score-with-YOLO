# 🎓 Classroom Attention Monitor with YOLO

YOLO tabanlı gerçek zamanlı sınıf dikkat takip sistemi. Öğretmenler ders anlatırken öğrencilerin dikkat seviyelerini ölçer ve analiz eder.

## 📋 Özellikler

### Öğretmen Uygulaması (Client)
- 🔐 Öğretmen giriş ve kayıt sistemi
- ➕ Yeni ders oluşturma
- 📹 Gerçek zamanlı kamera ile dikkat analizi
- 🎯 YOLO ile yüz/poz tespiti
- 😊 Duygu analizi
- 📊 Anlık dikkat skoru hesaplama
- ⏱️ Dakikalık metrik kayıtları
- 🔔 Düşük dikkat uyarıları

### Admin Dashboard (Web)
- 📊 Tüm derslerin genel istatistikleri
- 👨‍🏫 Öğretmen listesi ve performansları
- 📚 Ders listesi
- 📈 Oturum bazlı detaylı raporlar
- 📉 Dakikalık dikkat grafikleri
- 🔄 Otomatik yenileme

## 🚀 Kurulum

### Gereksinimler

```bash
pip install -r requirements.txt
```

### 1. Sunucuyu Başlat

```bash
python run_server.py
```

Sunucu http://localhost:5001 adresinde çalışacaktır.

### 2. Admin Kullanıcısı Oluştur

```bash
python create_admin.py
```

Bu script ile admin kullanıcısı oluşturabilirsiniz.

### 3. Test Öğretmen Kullanıcısı Oluştur (Opsiyonel)

```bash
python create_test_user.py
```

### 4. Öğretmen Uygulamasını Başlat

```bash
python main.py
```

## 📱 Kullanım

### Öğretmen Akışı

1. `python main.py` ile uygulamayı başlatın
2. **İlk kez kullanıyorsanız:** "Register" butonuna tıklayarak hesap oluşturun
3. Email ve şifre ile giriş yapın
4. Ders seçin veya yeni ders ekleyin ("+ Add New Course")
5. "Start Session" ile ders kaydını başlatın
6. Kamera dikkat skorlarını gerçek zamanlı gösterir
7. "End Session" ile dersi bitirin ve verileri kaydedin

### Admin Dashboard

1. Tarayıcıda `http://localhost:5001/dashboard` adresine gidin
2. Admin kullanıcı adı ve şifresi ile giriş yapın
3. Tüm öğretmen ve derslerin skorlarını görüntüleyin
4. Oturuma tıklayarak detaylı grafik görün

## 🏗️ Mimari

```
┌─────────────────┐     HTTP API     ┌─────────────────┐
│   Öğretmen      │ ◄──────────────► │    Flask        │
│   Uygulaması    │                  │    Server       │
│   (PyQt5)       │                  │                 │
└─────────────────┘                  └────────┬────────┘
                                              │
┌─────────────────┐                  ┌────────▼────────┐
│   Admin Web     │ ◄──────────────► │    SQLite       │
│   Dashboard     │     HTTP API     │    Database     │
└─────────────────┘                  └─────────────────┘
```

## 📁 Dosya Yapısı

```
├── server.py              # Flask API sunucusu
├── run_server.py          # Sunucu başlatıcı
├── client.py              # API client sınıfları
├── main.py                # Öğretmen uygulaması ana dosya
├── gui.py                 # Dikkat analizi GUI
├── login_window.py        # Giriş penceresi
├── yolo_model.py          # YOLO model wrapper
├── attention_analyzer.py  # Dikkat analizi
├── camera_manager.py      # Kamera yönetimi
├── create_admin.py        # Admin oluşturma script'i
├── create_test_user.py    # Test kullanıcısı oluşturma
├── config.py              # Yapılandırma
└── server/
    └── templates/
        └── dashboard.html # Admin dashboard
```

## 🔌 API Endpoints

### Öğretmen API'leri
- `POST /api/auth/register` - Kayıt
- `POST /api/auth/login` - Giriş
- `GET /api/courses` - Dersleri listele
- `POST /api/courses` - Ders oluştur
- `POST /api/sessions/start` - Oturum başlat
- `POST /api/sessions/{id}/minute` - Dakikalık metrik kaydet
- `POST /api/sessions/{id}/end` - Oturum bitir
- `GET /api/sessions` - Oturumları listele

### Admin API'leri
- `POST /api/admin/login` - Admin girişi
- `GET /api/admin/stats` - Genel istatistikler
- `GET /api/admin/teachers` - Tüm öğretmenler
- `GET /api/admin/courses` - Tüm dersler
- `GET /api/admin/sessions` - Tüm oturumlar
- `GET /api/admin/sessions/{id}` - Oturum detayı

## 📊 Dikkat Skoru Hesaplama

Dikkat skoru şu faktörlere göre hesaplanır:

1. **Baş Pozisyonu**: Öğrencinin yüzü kameraya dönük mü?
2. **Duygu Durumu**: Mutlu/nötr = dikkatli, üzgün/kızgın = dikkatsiz
3. **Hareket**: Aşırı hareket = dikkatsizlik

Skor 0-100 arasında bir değerdir:
- 🟢 70-100: Dikkatli
- 🟡 50-69: Orta
- 🔴 0-49: Dikkatsiz

## 🛠️ Teknolojiler

- **Backend**: Flask, Flask-SQLAlchemy, Flask-CORS
- **Frontend**: PyQt5 (Öğretmen App), HTML/CSS/JS (Dashboard)
- **AI/ML**: YOLOv8, OpenCV
- **Database**: SQLite
- **Auth**: JWT

## 📝 Lisans

MIT License

