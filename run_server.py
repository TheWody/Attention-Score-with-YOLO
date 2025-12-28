from server.app import app, db

def init_database():
    with app.app_context():
        db.create_all()
        print("✅ Veritabanı tabloları oluşturuldu.")

def main():
    print("=" * 50)
    print("🎓 Attention Monitor Server")
    print("=" * 50)

    init_database()

    import socket
    local_ip = socket.gethostbyname(socket.gethostname())

    print("\n📍 Server başlatılıyor...")
    print(f"   - Yerel IP: {local_ip}")
    print(f"   - API: http://{local_ip}:5001/api")
    print(f"   - Admin Dashboard: http://{local_ip}:5001/dashboard")
    print("\n💡 Diğer bilgisayardan bağlanmak için:")
    print(f"   Client'ta server URL'ini http://{local_ip}:5001 olarak ayarlayın")
    print("\n⚡ Durdurmak için Ctrl+C basın")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    main()
