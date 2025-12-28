import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import MainWindow
from login_window import LoginWindow
from client import APIClient


def main():
    """Main entry point with server integration."""
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        * {
            font-family: "Helvetica", "Arial";
        }
    """)

    SERVER_URL = "http://localhost:5001"

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