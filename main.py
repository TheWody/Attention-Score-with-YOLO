import sys
import json
import requests
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMessageBox, QInputDialog,
                              QDialog, QVBoxLayout, QLabel, QLineEdit,
                              QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt
from gui import MainWindow
from login_window import LoginWindow
from client import APIClient

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    return base_path / "client_config.json"

def load_config():
    config_path = get_config_path()
    default_config = {
        "server_url": "http://localhost:5001",
        "version": "1.0.0"
    }

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    save_config(default_config)
    return default_config

def save_config(config):
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Config kaydetme hatası: {e}")

def test_server_connection(url: str) -> bool:
    try:
        response = requests.get(f"{url}/api/admin/stats", timeout=5)
        return True  # Sunucu çalışıyor (401 bile olsa)
    except:
        try:
            response = requests.get(url, timeout=5)
            return True
        except:
            return False

class ServerConfigDialog(QDialog):

    def __init__(self, current_url: str, parent=None):
        super().__init__(parent)
        self.server_url = current_url
        self.setWindowTitle("Server Configuration")
        self.setFixedSize(450, 200)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("Server Connection")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        info = QLabel("Could not connect to server. Please enter the server address:")
        info.setStyleSheet("color: #666; font-size: 10pt;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.url_input = QLineEdit()
        self.url_input.setText(self.server_url)
        self.url_input.setPlaceholderText("http://192.168.1.100:5001")
        self.url_input.setMinimumHeight(40)
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12pt;
                background: white;
                color: #222;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
            QPushButton {
                background: #f0f0f0;
                color: #333;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton {
                background: #005bbb;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover { background: #004a99; }
        url = self.url_input.text().strip().rstrip('/')
        self.test_btn.setText("Testing...")
        self.test_btn.setEnabled(False)
        QApplication.processEvents()

        if test_server_connection(url):
            QMessageBox.information(self, "Success", "Connection successful!")
        else:
            QMessageBox.warning(self, "Failed", "Could not connect to server.\nMake sure the server is running.")

        self.test_btn.setText("Test Connection")
        self.test_btn.setEnabled(True)

    def save_and_connect(self):
        self.server_url = self.url_input.text().strip().rstrip('/')
        self.accept()

def main():
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        * {
            font-family: "Segoe UI", "Arial", sans-serif;
        }
        QLabel {
            color: #222222;
        }
        QLineEdit {
            color: #222222;
            background-color: white;
        }
        QComboBox {
            color: #222222;
            background-color: white;
        }
        QPushButton {
            color: #222222;
        }