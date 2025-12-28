import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

def build_client():
    print("=" * 50)
    print("Building Client (Teacher App)...")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AttentionMonitor",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"yolov8n-pose.pt{os.pathsep}.",
        "--add-data", f"yolov8n-cls.pt{os.pathsep}.",
        "--add-data", f"client_config.json{os.pathsep}.",
        "--hidden-import", "ultralytics",
        "--hidden-import", "ultralytics.nn.tasks",
        "--hidden-import", "cv2",
        "--hidden-import", "scipy.stats",
        "--hidden-import", "matplotlib.pyplot",
        "--hidden-import", "matplotlib.backends.backend_agg",
        "--hidden-import", "PyQt5.QtCore",
        "--hidden-import", "PyQt5.QtGui",
        "--hidden-import", "PyQt5.QtWidgets",
        "--collect-all", "ultralytics",
        "main.py"
    ]

    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        print("\n✅ Client build successful!")
        print(f"   Output: {BASE_DIR / 'dist' / 'AttentionMonitor'}")
    else:
        print("\n❌ Client build failed!")

    return result.returncode == 0

def build_server():
    print("=" * 50)
    print("Building Server (Admin Dashboard)...")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AttentionServer",
        "--console",  # Sunucu için konsol gerekli
        "--noconfirm",
        "--clean",
        "--add-data", f"server/templates{os.pathsep}server/templates",
        "--hidden-import", "flask",
        "--hidden-import", "flask_sqlalchemy",
        "--hidden-import", "flask_cors",
        "--hidden-import", "werkzeug",
        "--hidden-import", "werkzeug.security",
        "--hidden-import", "jwt",
        "--hidden-import", "sqlalchemy",
        "app_server.py"
    ]

    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        print("\n✅ Server build successful!")
        print(f"   Output: {BASE_DIR / 'dist' / 'AttentionServer'}")
    else:
        print("\n❌ Server build failed!")

    return result.returncode == 0

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage: python build.py [client|server|all]")
        return

    target = sys.argv[1].lower()

    if target == "client":
        build_client()
    elif target == "server":
        build_server()
    elif target == "all":
        success_client = build_client()
        success_server = build_server()

        print("\n" + "=" * 50)
        print("BUILD SUMMARY")
        print("=" * 50)
        print(f"Client: {'✅ Success' if success_client else '❌ Failed'}")
        print(f"Server: {'✅ Success' if success_server else '❌ Failed'}")

        if success_client and success_server:
            print("\n📦 Both applications are ready in 'dist' folder!")
            print("\nTo run:")
            print("  1. First start: dist\\AttentionServer\\AttentionServer.exe")
            print("  2. Then start:  dist\\AttentionMonitor\\AttentionMonitor.exe")
            print("  3. Admin dashboard: http://localhost:5001/dashboard")
    else:
        print(f"Unknown target: {target}")
        print("Use: client, server, or all")

if __name__ == "__main__":
    main()
