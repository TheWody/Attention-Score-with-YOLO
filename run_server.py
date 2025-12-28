from app_server import app, db

def init_database():
    with app.app_context():
        db.create_all()
        print("✅ Veritabanı tabloları oluşturuldu.")

def main():
    print("=" * 50)
    print("🎓 Attention Monitor Server")
    print("=" * 50)

    init_database()

    print("\n📍 Server başlatılıyor...")
    print("   - API: http://localhost:5001/api")
    print("   - Admin Dashboard: http://localhost:5001/dashboard")
    print("\n⚡ Durdurmak için Ctrl+C basın")
    print("=" * 50 + "\n")

    app.run(host='127.0.0.1', port=5001, debug=True)

if __name__ == '__main__':
    main()
