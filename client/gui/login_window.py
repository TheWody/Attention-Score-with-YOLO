from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from client import APIClient


class LoginWindow(QDialog):

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.selected_course = None
        self.setWindowTitle("Classroom Attention Monitor - Login")
        self.setFixedSize(500, 480)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)

        title = QLabel("Teacher Login")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #222;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Access your classroom analytics")
        subtitle.setStyleSheet("color: #666; font-size: 11pt;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("teacher@university.edu")
        self.email_input.setMinimumHeight(45)
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12pt;
                background: white;
                color: #222;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
        """)
        layout.addWidget(self.email_input)

        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12pt;
                background: white;
                color: #222;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
        """)
        self.password_input.returnPressed.connect(self.on_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(45)
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

        layout.addSpacing(10)

        register_link = QPushButton("Don't have an account? Register here")
        register_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #005bbb;
                border: none;
                font-size: 10pt;
                font-weight: 600;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #003d7a;
            }
        """)
        register_link.clicked.connect(self.on_register)
        layout.addWidget(register_link)

        layout.addStretch()

    def on_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")

        if self.api_client.login(email, password):
            courses = self.api_client.get_courses()

            if not courses:
                reply = QMessageBox.question(
                    self,
                    "No Courses",
                    "You don't have any courses yet.\nWould you like to add a new course?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    add_dialog = AddCourseDialog(self.api_client, self)
                    if add_dialog.exec_() == QDialog.Accepted and add_dialog.new_course:
                        courses = [add_dialog.new_course]
                    else:
                        self.login_btn.setEnabled(True)
                        self.login_btn.setText("Login")
                        return
                else:
                    self.login_btn.setEnabled(True)
                    self.login_btn.setText("Login")
                    return

            course_dialog = CourseSelectionDialog(courses, self, self.api_client)
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

    def on_register(self):
        register_dialog = RegisterDialog(self.api_client, self)
        if register_dialog.exec_() == QDialog.Accepted:
            self.email_input.setText(register_dialog.registered_email)
            self.password_input.setFocus()
            QMessageBox.information(
                self,
                "Registration Successful",
                "Your account has been created. Please login with your credentials."
            )


class AddCourseDialog(QDialog):

    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.new_course = None
        self.setWindowTitle("Add New Course")
        self.setFixedSize(400, 400)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)

        title = QLabel("Add New Course")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #222;")
        layout.addWidget(title)

        layout.addSpacing(10)

        input_style = """
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12pt;
                background: white;
                color: #222;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
        """

        code_label = QLabel("Course Code:")
        code_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(code_label)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("e.g. CS101")
        self.code_input.setStyleSheet(input_style)
        layout.addWidget(self.code_input)

        name_label = QLabel("Course Name:")
        name_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Introduction to Programming")
        self.name_input.setStyleSheet(input_style)
        layout.addWidget(self.name_input)

        location_label = QLabel("Classroom Location (optional):")
        location_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(location_label)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g. Room 101")
        self.location_input.setStyleSheet(input_style)
        layout.addWidget(self.location_input)

        semester_label = QLabel("Semester (optional):")
        semester_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(semester_label)

        self.semester_input = QLineEdit()
        self.semester_input.setPlaceholderText("e.g. Fall 2024")
        self.semester_input.setStyleSheet(input_style)
        layout.addWidget(self.semester_input)

        layout.addSpacing(10)

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

        self.add_btn = QPushButton("Add Course")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #005bbb;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #004a99;
            }
        """)
        self.add_btn.clicked.connect(self.on_add)
        button_layout.addWidget(self.add_btn)

        layout.addLayout(button_layout)

    def on_add(self):
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        location = self.location_input.text().strip()
        semester = self.semester_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Error", "Please enter course code")
            return

        if not name:
            QMessageBox.warning(self, "Error", "Please enter course name")
            return

        self.add_btn.setEnabled(False)
        self.add_btn.setText("Adding...")

        course_id = self.api_client.create_course(code, name, location, semester)

        if course_id:
            self.new_course = {
                'course_id': course_id,
                'course_code': code,
                'course_name': name,
                'classroom_location': location,
                'semester': semester
            }
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to create course")
            self.add_btn.setEnabled(True)
            self.add_btn.setText("Add Course")


class RegisterDialog(QDialog):

    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.registered_email = None
        self.setWindowTitle("Teacher Registration")
        self.setFixedSize(450, 550)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        title = QLabel("Create Account")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #222;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Register as a new teacher")
        subtitle.setStyleSheet("color: #666; font-size: 11pt;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(15)

        name_label = QLabel("Full Name:")
        name_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("John Doe")
        self.name_input.setStyleSheet(self._input_style())
        layout.addWidget(self.name_input)

        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("teacher@university.edu")
        self.email_input.setStyleSheet(self._input_style())
        layout.addWidget(self.email_input)

        dept_label = QLabel("Department (optional):")
        dept_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(dept_label)

        self.dept_input = QLineEdit()
        self.dept_input.setPlaceholderText("Computer Engineering")
        self.dept_input.setStyleSheet(self._input_style())
        layout.addWidget(self.dept_input)

        password_label = QLabel("Password:")
        password_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Min 6 characters")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(self._input_style())
        layout.addWidget(self.password_input)

        confirm_label = QLabel("Confirm Password:")
        confirm_label.setStyleSheet("color: #333; font-size: 10pt; font-weight: 500;")
        layout.addWidget(confirm_label)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Re-enter password")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setStyleSheet(self._input_style())
        layout.addWidget(self.confirm_input)

        layout.addSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e0e0e0;
                color: #333;
                padding: 12px 20px;
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

        self.register_btn = QPushButton("Register")
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: #29b566;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #22a055;
            }
        """)
        self.register_btn.clicked.connect(self.on_register)
        button_layout.addWidget(self.register_btn)

        layout.addLayout(button_layout)

    def _input_style(self):
        return """
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12pt;
                background: white;
                color: #222;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #005bbb;
            }
        """

    def on_register(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        department = self.dept_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter your name")
            return

        if not email or '@' not in email:
            QMessageBox.warning(self, "Error", "Please enter a valid email")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        self.register_btn.setEnabled(False)
        self.register_btn.setText("Registering...")

        if self.api_client.register(name, email, password, department):
            self.registered_email = email
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Registration Failed",
                "Could not create account. Email might already be in use."
            )
            self.register_btn.setEnabled(True)
            self.register_btn.setText("Register")


class CourseSelectionDialog(QDialog):

    def __init__(self, courses, parent=None, api_client=None):
        super().__init__(parent)
        self.courses = courses
        self.api_client = api_client
        self.selected_course = None
        self.setWindowTitle("Select Course")
        self.setFixedSize(400, 350)
        self.setStyleSheet("background: #f5f5f5;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        title = QLabel("Select Your Course")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #222;")
        layout.addWidget(title)

        subtitle = QLabel("Choose which class you're teaching today")
        subtitle.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        self.course_combo = QComboBox()
        self.course_combo.setStyleSheet("""
            QComboBox {
                padding: 12px 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12pt;
                background: white;
                color: #222;
            }
            QComboBox:focus {
                border: 2px solid #005bbb;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #222;
                selection-background-color: #005bbb;
                selection-color: white;
            }
        """)
        self._populate_courses()
        layout.addWidget(self.course_combo)

        add_course_link = QPushButton("+ Add New Course")
        add_course_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #005bbb;
                border: none;
                font-size: 10pt;
                font-weight: 600;
                text-align: left;
                padding: 5px 0;
            }
            QPushButton:hover {
                color: #003d7a;
                text-decoration: underline;
            }
        """)
        add_course_link.clicked.connect(self.show_add_course_dialog)
        layout.addWidget(add_course_link)

        layout.addSpacing(10)

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

    def _populate_courses(self):
        self.course_combo.clear()
        for course in self.courses:
            display_text = f"{course['course_code']} - {course['course_name']}"
            if course.get('classroom_location'):
                display_text += f" ({course['classroom_location']})"
            self.course_combo.addItem(display_text, course)

    def show_add_course_dialog(self):
        if not self.api_client:
            QMessageBox.warning(self, "Error", "Cannot add course at this time")
            return

        add_dialog = AddCourseDialog(self.api_client, self)
        if add_dialog.exec_() == QDialog.Accepted:
            new_course = add_dialog.new_course
            if new_course:
                self.courses.append(new_course)
                self._populate_courses()
                self.course_combo.setCurrentIndex(len(self.courses) - 1)

    def on_select(self):
        self.selected_course = self.course_combo.currentData()
        self.accept()

