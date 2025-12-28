import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from client.gui import MainWindow, LoginWindow
from client import APIClient


def load_config():
    config_path = Path(__file__).parent / "client" / "config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('server_url', 'http://localhost:5001')
    except Exception:
        return 'http://localhost:5001'


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        * {
            font-family: "Helvetica", "Arial";
        }
    """)

    SERVER_URL = load_config()
    print(f"Server URL: {SERVER_URL}")

    api_client = APIClient(base_url=SERVER_URL)

    login_window = LoginWindow(api_client)
    if login_window.exec_() != LoginWindow.Accepted:
        sys.exit(0)

    selected_course = login_window.selected_course
    teacher_info = api_client.teacher_info

    if not selected_course or not teacher_info:
        QMessageBox.critical(None, "Error", "Failed to load course information")
        sys.exit(1)

    window = MainWindow(api_client, selected_course, teacher_info)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()