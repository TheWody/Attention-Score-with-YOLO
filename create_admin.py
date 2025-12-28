from app_server import app, db, Admin
from werkzeug.security import generate_password_hash

def create_admin():

    print("=" * 50)
    print("🔐 Admin Kullanıcı Oluşturma")
    print("=" * 50)

    username = input("\nKullanıcı adı: ").strip()
    if not username:
        print("❌ Kullanıcı adı boş olamaz!")
        return

    password = input("Şifre: ").strip()
    if not password:
        print("❌ Şifre boş olamaz!")
        return

    name = input("İsim (görüntülenecek): ").strip()
    if not name:
        name = username

    with app.app_context():
        if Admin.query.filter_by(username=username).first():
            print(f"\n❌ '{username}' kullanıcı adı zaten mevcut!")
            return

        admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
            name=name
        )

        db.session.add(admin)
        db.session.commit()

        print(f"\n✅ Admin kullanıcısı başarıyla oluşturuldu!")
        print(f"   Kullanıcı adı: {username}")
        print(f"   İsim: {name}")
        print(f"\n🌐 Dashboard: http://localhost:5001/dashboard")

def list_admins():
    with app.app_context():
        admins = Admin.query.all()

        if not admins:
            print("\n📋 Henüz admin kullanıcısı yok.")
            return

        print("\n📋 Mevcut Admin Kullanıcıları:")
        print("-" * 40)
        for admin in admins:
            print(f"  • {admin.username} ({admin.name})")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    print("\n1. Yeni admin oluştur")
    print("2. Mevcut adminleri listele")

    choice = input("\nSeçiminiz (1/2): ").strip()

    if choice == '1':
        create_admin()
    elif choice == '2':
        list_admins()
    else:
        print("Geçersiz seçim!")
