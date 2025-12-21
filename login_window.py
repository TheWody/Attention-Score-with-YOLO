from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from client import APIClient


class LoginWindow(QDialog):
    """Hoca giriş penceresi."""

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.selected_course = None
        self.setWindowTitle("Classroom Attention Monitor - Login")
        self.setFixedSize(450, 350)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        # Title
        title = QLabel("Teacher Login")
        title.setFont(QFont("Helvetica", 20, QFont.Bold))
        title.setStyleSheet("color: #222;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Access your classroom analytics")
        subtitle.setStyleSheet("color: #666; font-size: 11pt;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Email
        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("teacher@university.edu")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 11pt;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
        """)
        layout.addWidget(self.email_input)

        # Password
        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 11pt;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
        """)
        self.password_input.returnPressed.connect(self.on_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        # Login Button
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #005bbb;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #004a99;
            }
            QPushButton:pressed {
                background: #003d7a;
            }
        """)
        self.login_btn.clicked.connect(self.on_login)
        layout.addWidget(self.login_btn)

        layout.addStretch()

    def on_login(self):
        """Giriş yapma işlemi."""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")

        if self.api_client.login(email, password):
            # Dersleri getir ve seçim yap
            courses = self.api_client.get_courses()

            if not courses:
                QMessageBox.warning(
                    self,
                    "No Courses",
                    "You don't have any courses. Please contact administrator."
                )
                self.login_btn.setEnabled(True)
                self.login_btn.setText("Login")
                return

            # Ders seçim dialogu
            course_dialog = CourseSelectionDialog(courses, self)
            if course_dialog.exec_() == QDialog.Accepted:
                self.selected_course = course_dialog.selected_course
                self.accept()
            else:
                self.login_btn.setEnabled(True)
                self.login_btn.setText("Login")
        else:
            QMessageBox.critical(
                self,
                "Login Failed",
                "Invalid credentials. Please try again."
            )
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Login")


class CourseSelectionDialog(QDialog):
    """Ders seçim dialogu."""

    def __init__(self, courses, parent=None):
        super().__init__(parent)
        self.courses = courses
        self.selected_course = None
        self.setWindowTitle("Select Course")
        self.setFixedSize(400, 250)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        """UI bileşenlerini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # Title
        title = QLabel("Select Your Course")
        title.setFont(QFont("Helvetica", 16, QFont.Bold))
        title.setStyleSheet("color: #222;")
        layout.addWidget(title)

        subtitle = QLabel("Choose which class you're teaching today")
        subtitle.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # Course dropdown
        self.course_combo = QComboBox()
        self.course_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 11pt;
                background: white;
            }
            QComboBox:focus {
                border: 2px solid #005bbb;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)

        for course in self.courses:
            display_text = f"{course['course_code']} - {course['course_name']}"
            if course.get('classroom_location'):
                display_text += f" ({course['classroom_location']})"
            self.course_combo.addItem(display_text, course)

        layout.addWidget(self.course_combo)

        layout.addSpacing(10)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e0e0e0;
                color: #333;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #d0d0d0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Start Session")
        select_btn.setStyleSheet("""
            QPushButton {
                background: #29b566;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #22a055;
            }
        """)
        select_btn.clicked.connect(self.on_select)
        button_layout.addWidget(select_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def on_select(self):
        """Ders seçildiğinde."""
        self.selected_course = self.course_combo.currentData()
        self.accept()