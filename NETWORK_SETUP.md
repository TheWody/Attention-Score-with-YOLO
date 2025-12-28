# İki Bilgisayar Arası Bağlantı Kurulumu

Bu rehber, Attention Monitor uygulamasını iki farklı bilgisayarda çalıştırmak için gereken adımları açıklar.

## Gereksinimler

- Her iki bilgisayar da **aynı ağa** (WiFi veya LAN) bağlı olmalıdır
- Windows Firewall'da 5001 portu açık olmalıdır

---

## 1. Server Bilgisayarı (Ana Bilgisayar)

### Adım 1: Server'ı Başlat

```bash
python run_server.py
```

veya

```bash
StartDashboard.bat
```

Server başladığında şöyle bir çıktı göreceksiniz:

```
==================================================
🎓 Attention Monitor Server
==================================================

📍 Server başlatılıyor...
   - Yerel IP: 192.168.1.100
   - API: http://192.168.1.100:5001/api
   - Admin Dashboard: http://192.168.1.100:5001/dashboard

💡 Diğer bilgisayardan bağlanmak için:
   Client'ta server URL'ini http://192.168.1.100:5001 olarak ayarlayın
```

**ÖNEMLİ**: `Yerel IP` kısmındaki IP adresini not alın (örnek: `192.168.1.100`)

### Adım 2: Windows Firewall'u Yapılandır

1. Windows Arama'ya "Windows Defender Firewall" yazın
2. "Gelişmiş Ayarlar" tıklayın
3. Sol menüden "Gelen Kuralları" seçin
4. Sağ menüden "Yeni Kural" tıklayın
5. "Port" seçin → İleri
6. "TCP" ve "Belirli yerel bağlantı noktaları: 5001" yazın → İleri
7. "Bağlantıya izin ver" → İleri
8. Tüm profilleri işaretli bırakın → İleri
9. Kural adı: "Attention Monitor Server" → Bitir

---

## 2. Client Bilgisayarı (Öğretmen Bilgisayarı)

### Adım 1: config.json Dosyasını Düzenle

`client/config.json` dosyasını açın ve server IP adresini yazın:

```json
{
    "server_url": "http://192.168.1.100:5001",
    "version": "1.0.0"
}
```

**NOT**: `192.168.1.100` yerine server bilgisayarının IP adresini yazın!

### Adım 2: Client'ı Başlat

```bash
python main.py
```

veya

```bash
StartClient.bat
```

---

## Bağlantı Testi

### Server'a Erişimi Test Et

Client bilgisayarından tarayıcıyı açın ve şu adresi yazın:

```
http://192.168.1.100:5001/api/health
```

Eğer `{"status": "ok"}` görüyorsanız bağlantı başarılıdır.

---

## Sorun Giderme

### "Bağlantı reddedildi" hatası

1. Server bilgisayarında server'ın çalıştığından emin olun
2. Firewall kuralını doğru oluşturduğunuzdan emin olun
3. Her iki bilgisayarın aynı ağda olduğunu kontrol edin

### IP adresi nasıl bulunur?

Server bilgisayarında:

```powershell
ipconfig
```

"IPv4 Address" satırındaki adresi kullanın (örnek: 192.168.1.100)

### Farklı ağlardaysanız

Farklı ağlardaysanız (örneğin evde ve okulda), VPN veya port forwarding gerekir. Bu daha karmaşık bir yapılandırmadır.

---

## Özet

| Bilgisayar | Yapılacak İşlem |
|------------|-----------------|
| **Server** | `run_server.py` çalıştır, IP adresini not al |
| **Client** | `config.json`'a server IP'sini yaz, `main.py` çalıştır |

---

## Dashboard'a Erişim

Admin dashboard'a herhangi bir bilgisayardan erişebilirsiniz:

```
http://[SERVER_IP]:5001/dashboard
```

Örnek: `http://192.168.1.100:5001/dashboard`

Varsayılan admin bilgileri:
- Kullanıcı adı: `admin`
- Şifre: `admin123`

