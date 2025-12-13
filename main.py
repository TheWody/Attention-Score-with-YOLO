import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        * {
            font-family: "Helvetica", "Arial";
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
