import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import deque
import json

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QSizePolicy, QSpacerItem, QLineEdit, QMessageBox
)

from camera_manager import CameraFeedManager
from yolo_model import YOLOModel
from attention_analyzer import AttentionAnalyzer
from database_manager import DatabaseManager


class VideoProcessingThread(QThread):
    """Processes frames using YOLO and attention analysis in a separate thread."""
    frame_ready = pyqtSignal(np.ndarray, list)
    fps_updated = pyqtSignal(float)
    metrics_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False
        self.camera = None
        self.yolo = None
        self.analyzer = None

    def initialize_models(self):
        """Initialize YOLO and analyzer models."""
        try:
            print("Initializing models...")
            self.camera = CameraFeedManager(source=0)
            self.yolo = YOLOModel()
            self.analyzer = AttentionAnalyzer()
            print("Models initialized successfully!")
            return True
        except Exception as e:
            print(f"Error initializing models: {e}")
            return False

    def run(self):
        if not self.initialize_models():
            return

        if not self.camera.is_running:
            print("Error: Camera not running")
            return

        self.running = True
        frame_times = deque(maxlen=30)

        while self.running:
            success, frame = self.camera.read_frame()
            if not success:
                break

            frame_times.append(cv2.getTickCount())
            if len(frame_times) > 1:
                fps = (len(frame_times) - 1) / (
                        (frame_times[-1] - frame_times[0]) / cv2.getTickFrequency()
                )
                self.fps_updated.emit(fps)

            results = self.yolo.detect_pose(frame)
            student_data = self.yolo.extract_and_analyze(results, frame)

            processed_data = []
            total_score = 0
            attentive_count = 0
            distracted_count = 0

            for data in student_data:
                pose_state = self.analyzer.analyze_head_pose(data['keypoints'])
                emotion_label = data['emotion_label']
                score = self.analyzer.calculate_attention_score(pose_state, emotion_label)

                data['pose_state'] = pose_state
                data['score'] = score
                processed_data.append(data)

                total_score += score
                if score >= 70:
                    attentive_count += 1
                else:
                    distracted_count += 1

            avg_score = int(total_score / len(processed_data)) if processed_data else 0

            annotated_frame = self.annotate_frame(frame.copy(), processed_data)

            metrics = {
                'avg_score': avg_score,
                'total_students': len(processed_data),
                'attentive': attentive_count,
                'distracted': distracted_count
            }

            self.frame_ready.emit(annotated_frame, processed_data)
            self.metrics_updated.emit(metrics)

            cv2.waitKey(1)

        if self.camera:
            self.camera.release()

    def annotate_frame(self, frame, student_data):
        """Draw bounding boxes and scores on frame."""
        for data in student_data:
            bbox = data['bbox']
            score = data['score']
            pose_state = data['pose_state']
            emotion_label = data['emotion_label']

            color = (0, 255, 0) if score >= 70 else (0, 0, 255)
            x_min, y_min, x_max, y_max = map(int, bbox)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)

            text_score = f"Score: {score} ({pose_state})"
            text_emotion = f"Emotion: {emotion_label.upper()}"

            cv2.putText(frame, text_score, (x_min, y_min - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, text_emotion, (x_min, y_min - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return frame

    def stop(self):
        self.running = False
        self.wait()


class MetricsTracker:
    """Tracks attention metrics over time."""

    def __init__(self, history_size=100):
        self.scores = deque(maxlen=history_size)
        self.history_size = history_size
        self.frame_count = 0
        self.distracted_frames = 0

    def add_score(self, score):
        self.scores.append(score)
        self.frame_count += 1
        if score < 50:
            self.distracted_frames += 1

    def rolling_avg(self):
        return np.mean(self.scores) if self.scores else 0

    def peak(self):
        return max(self.scores) if self.scores else 0

    def distraction_pct(self):
        if self.frame_count == 0:
            return 0
        return (self.distracted_frames / self.frame_count) * 100

    def reset(self):
        self.scores.clear()
        self.frame_count = 0
        self.distracted_frames = 0


class MinuteTracker:
    """Her dakika için metrikleri takip eder."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.scores = []
        self.attentive_counts = []
        self.distracted_counts = []
        self.frame_count = 0

    def add_data(self, score, attentive, distracted):
        self.scores.append(score)
        self.attentive_counts.append(attentive)
        self.distracted_counts.append(distracted)
        self.frame_count += 1

    def get_summary(self):
        if not self.scores:
            return None

        return {
            'avg_score': np.mean(self.scores),
            'min_score': int(min(self.scores)),
            'max_score': int(max(self.scores)),
            'avg_attentive': int(np.mean(self.attentive_counts)),
            'avg_distracted': int(np.mean(self.distracted_counts)),
            'total_frames': self.frame_count
        }


class StatCard(QFrame):
    """Widget for displaying a metric card."""

    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 12px;
            }
            QLabel {
                font-family: "Helvetica", "Arial";
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #555; font-size: 11pt;")

        self.value_label = QLabel(str(value))
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.value_label.setStyleSheet("font-weight: 600; font-size: 18pt; color: #222;")

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)


class MainWindow(QMainWindow):
    """Main application window with camera feed and metrics display."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Classroom Attention Monitor - Real-Time Detection")
        self.resize(1200, 500)

        self.is_running = False
        self.metrics = MetricsTracker()
        self.video_thread = None
        self.session_start = None
        self.session_data = []

        # Veritabanı yöneticisi
        self.db = DatabaseManager()
        self.current_session_id = None

        # Dakikalık takip
        self.minute_tracker = MinuteTracker()
        self.current_minute = 0
        self.last_minute_save = None

        self.snooze_timer = QTimer()
        self.snooze_timer.setSingleShot(True)
        self.snooze_timer.timeout.connect(self._on_snooze_end)
        self.is_snoozed = False

        self.alert_timer = QTimer()
        self.alert_timer.setSingleShot(True)
        self.alert_timer.timeout.connect(self._on_alert_timeout)
        self.alert_display_seconds = 8

        self.current_attentive = 0
        self.current_distracted = 0
        self.current_total = 0
        self.alert_pct = 40.0

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        central = QWidget()
        central.setStyleSheet("background: #3c3c3c;")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(16)

        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(24)
        main_layout.addLayout(mid_layout)

        left_card = self._create_left_panel()
        mid_layout.addWidget(left_card, 3)

        right_card = self._create_right_panel()
        mid_layout.addWidget(right_card, 2)

        self.banner = self._create_alert_banner()
        main_layout.addWidget(self.banner)

    def _create_left_panel(self):
        """Create left panel with camera feed."""
        left_card = QFrame()
        left_card.setStyleSheet("""
            QFrame {
                background: #e5e5e5;
                border-radius: 20px;
            }
            QLabel {
                font-family: "Helvetica", "Arial";
            }
        """)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(24, 20, 24, 20)
        left_layout.setSpacing(12)

        top_left_row = QHBoxLayout()
        self.course_label = QLineEdit("EEE 302 | Real-Time Detection")
        self.course_label.setFrame(False)
        self.course_label.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 16pt;
                font-weight: 600;
                color: #222;
                border: 1px solid #dddddd;
            }
        """)
        self.course_label.textChanged.connect(self._adjust_title_width)
        top_left_row.addWidget(self.course_label, 0, Qt.AlignLeft)
        top_left_row.addStretch(1)

        self.time_badge = QLabel("Time: 00:00:00")
        self.time_badge.setAlignment(Qt.AlignCenter)
        self.time_badge.setFixedHeight(20)
        self.time_badge.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-radius: 14px;
                padding: 4px 12px;
                font-size: 11pt;
                border: 1px solid #dddddd;
                color: #333;
            }
        """)
        top_left_row.addWidget(self.time_badge)
        left_layout.addLayout(top_left_row)

        subtitle = QLabel("Classroom View - YOLO Detection")
        subtitle.setStyleSheet('font-size: 15pt; color: #555;')
        left_layout.addWidget(subtitle)

        self.view_label = QLabel()
        self.view_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view_label.setMaximumHeight(800)
        self.view_label.setStyleSheet("""
            QLabel {
                background: #f7f7f7;
                border-radius: 14px;
                border: 1px solid #dddddd;
            }
        """)
        self.view_label.setAlignment(Qt.AlignCenter)
        self.view_label.setText("Camera will appear here\nClick 'Start' to begin real-time detection")
        left_layout.addWidget(self.view_label)

        button_layout = self._create_control_buttons()
        left_layout.addLayout(button_layout)

        return left_card

    def _create_control_buttons(self):
        """Create control buttons layout."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.save_btn = QPushButton("Export JSON")
        self.reset_btn = QPushButton("Reset")

        self.start_btn.setStyleSheet(
            "QPushButton { background: #29b566; color: white; "
            'border-radius: 18px; padding: 6px 20px; font-weight: 600; }'
        )
        self.stop_btn.setStyleSheet(
            "QPushButton { background: #e84545; color: white; "
            'border-radius: 18px; padding: 6px 20px; font-weight: 600; }'
        )
        base_button_style = (
            'QPushButton { background: #ffffff; color: #222; '
            'border-radius: 18px; padding: 6px 18px; '
            'border: 1px solid #cfcfcf; }'
        )
        self.save_btn.setStyleSheet(base_button_style)
        self.reset_btn.setStyleSheet(base_button_style)

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.save_btn.clicked.connect(self.on_save)
        self.reset_btn.clicked.connect(self.on_reset)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch(1)

        return button_layout

    def _create_right_panel(self):
        """Create right panel with metrics."""
        right_card = QFrame()
        right_card.setStyleSheet("""
            QFrame {
                background: #f0f0f0;
                border-radius: 20px;
            }
            QLabel {
                font-family: "Helvetica", "Arial";
            }
        """)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(24, 20, 24, 20)
        right_layout.setSpacing(14)

        title_label = QLabel("Attention Score")
        title_label.setStyleSheet("font-size: 16pt; font-weight: 600; color: #222;")
        right_layout.addWidget(title_label)

        self.score_label = QLabel("—")
        self.score_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.score_label.setStyleSheet("font-size: 40pt; font-weight: 700; color: #005bbb;")
        right_layout.addWidget(self.score_label)

        desc_label = QLabel("0 = low attention, 100 = high")
        desc_label.setStyleSheet("font-size: 10pt; color: #555;")
        right_layout.addWidget(desc_label)

        grid = self._create_stat_cards()
        right_layout.addLayout(grid)
        right_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        return right_card

    def _create_stat_cards(self):
        """Create grid of stat cards."""
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_avg = StatCard("Avg (rolling)", "—")
        self.card_peak = StatCard("Peak", "—")
        self.card_distr_pct = StatCard("Distracted %", "—")
        self.card_fps = StatCard("FPS", "—")
        self.card_students_att = StatCard("Students (attent.)", "—")
        self.card_students_dist = StatCard("Students (distr.)", "—")

        grid.addWidget(self.card_avg, 0, 0)
        grid.addWidget(self.card_peak, 0, 1)
        grid.addWidget(self.card_distr_pct, 0, 2)
        grid.addWidget(self.card_fps, 1, 0)
        grid.addWidget(self.card_students_att, 1, 1)
        grid.addWidget(self.card_students_dist, 1, 2)

        return grid

    def _create_alert_banner(self):
        """Create alert banner."""
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: #ffe0df;
                border-radius: 14px;
            }
        """)
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(18, 10, 18, 10)
        banner_layout.setSpacing(16)

        self.warn_label = QLabel("⚠ Low attention detected — please re-engage the class")
        self.warn_label.setStyleSheet("color: #a32020; font-size: 11pt; padding: 6px 10px;")
        self.warn_label.setWordWrap(True)
        self.warn_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        banner_layout.addWidget(self.warn_label, 1)

        self.ack_btn = QPushButton("Acknowledge (snooze 30s)")
        self.ack_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #222;
                border-radius: 18px;
                padding: 6px 18px;
                border: 1px solid #e0b3b2;
                font-weight: 500;
            }
        """)
        self.ack_btn.clicked.connect(self._on_acknowledge)
        banner_layout.addWidget(self.ack_btn, 0, Qt.AlignRight)

        banner.setVisible(False)
        return banner

    def _adjust_title_width(self, text):
        """Adjust title width based on content."""
        fm = self.course_label.fontMetrics()
        content_width = fm.horizontalAdvance(text or "EEE 302")
        padding = 20
        max_width = max(150, self.width() - self.time_badge.width() - 60)
        new_width = min(content_width + padding, max_width)
        self.course_label.setFixedWidth(new_width)

    def _cleanup_resources(self):
        """Clean up threads and timers."""
        if hasattr(self, 'video_thread') and self.video_thread:
            try:
                self.video_thread.frame_ready.disconnect()
                self.video_thread.fps_updated.disconnect()
                self.video_thread.metrics_updated.disconnect()
            except:
                pass
            self.video_thread.stop()
            self.video_thread = None

    def _save_minute_data(self):
        """Dakikalık verileri veritabanına kaydeder."""
        if self.current_session_id is None:
            return

        summary = self.minute_tracker.get_summary()
        if summary is None:
            return

        self.db.save_minute_metric(
            session_id=self.current_session_id,
            minute_number=self.current_minute,
            avg_score=summary['avg_score'],
            min_score=summary['min_score'],
            max_score=summary['max_score'],
            avg_attentive=summary['avg_attentive'],
            avg_distracted=summary['avg_distracted'],
            total_frames=summary['total_frames']
        )

        # Yeni dakika için sıfırla
        self.current_minute += 1
        self.minute_tracker.reset()

    def on_start(self):
        """Start camera capture and detection."""
        if self.is_running:
            return

        self._cleanup_resources()
        self.is_running = True
        self.session_start = datetime.now()
        self.session_data = []
        self.metrics.reset()
        self.start_btn.setEnabled(False)

        # Veritabanında yeni session başlat
        course_name = self.course_label.text() or "Unknown Course"
        self.current_session_id = self.db.start_session(course_name)

        # Dakikalık takibi sıfırla
        self.current_minute = 0
        self.minute_tracker.reset()
        self.last_minute_save = datetime.now()

        self.video_thread = VideoProcessingThread()
        self.video_thread.frame_ready.connect(self._on_frame_ready)
        self.video_thread.fps_updated.connect(self._on_fps_updated)
        self.video_thread.metrics_updated.connect(self._on_metrics_updated)
        self.video_thread.start()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(100)

    def on_stop(self):
        """Stop camera capture."""
        if not self.is_running:
            return

        self.is_running = False

        # Son dakikanın verilerini kaydet
        if self.minute_tracker.frame_count > 0:
            self._save_minute_data()

        # Session'ı sonlandır
        if self.current_session_id is not None:
            final_avg = self.db.end_session(
                session_id=self.current_session_id,
                avg_attention_score=self.metrics.rolling_avg(),
                peak_score=int(self.metrics.peak()),
                total_students=self.current_total,
                total_frames=self.metrics.frame_count
            )

            # Sonucu göster
            duration = (datetime.now() - self.session_start).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)

            msg = QMessageBox(self)
            msg.setWindowTitle("Session Completed")
            msg.setText(f"Session {self.current_session_id} has been completed")
            msg.setInformativeText(
                f"Duration: {minutes} minutes {seconds} seconds\n"
                f"Average Attention Score: {final_avg:.1f}\n"
                f"Peak Score: {int(self.metrics.peak())}\n"
                f"Total Frames: {self.metrics.frame_count}"
            )
            msg.setIcon(QMessageBox.Information)
            msg.exec_()

        self._cleanup_resources()
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        self.start_btn.setEnabled(True)
        self.view_label.setText("Camera stopped.\nClick 'Start' to resume")

    def on_save(self):
        """Export session data to JSON."""
        if self.current_session_id is None:
            self.warn_label.setText("⚠ No active session to export.")
            self.warn_label.setStyleSheet("color: #a32020; font-size: 11pt;")
            self.banner.setVisible(True)
            return

        filepath = self.db.export_session_to_json(self.current_session_id)
        if filepath:
            self.warn_label.setText(f"✓ Session exported to: {filepath}")
            self.warn_label.setStyleSheet("color: #228b22; font-size: 11pt;")
            self.banner.setVisible(True)

    def on_reset(self):
        """Reset all metrics."""
        self.on_stop()
        self.metrics.reset()
        self.session_data = []
        self.session_start = None
        self.current_session_id = None
        self.current_minute = 0
        self.minute_tracker.reset()
        self._update_all_labels()
        self.view_label.setText("Reset complete.\nClick 'Start' to begin")
        self.banner.setVisible(False)

    def _on_acknowledge(self):
        """Snooze alert."""
        self.is_snoozed = True
        self.banner.setVisible(False)
        if self.alert_timer.isActive():
            self.alert_timer.stop()
        self.snooze_timer.start(30000)

    def _on_snooze_end(self):
        """Called when snooze ends."""
        self.is_snoozed = False

    def _on_alert_timeout(self):
        """Hide banner after alert timeout."""
        if not self.is_snoozed:
            self.banner.setVisible(False)

    def _on_frame_ready(self, frame, student_data):
        """Display frame in UI."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = 3 * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaledToHeight(380, Qt.SmoothTransformation)
        self.view_label.setPixmap(scaled_pixmap)

    def _on_fps_updated(self, fps):
        """Update FPS display."""
        self.card_fps.value_label.setText(f"{fps:.1f}")

    def _on_metrics_updated(self, metrics):
        """Update metrics from detection."""
        score = metrics['avg_score']
        self.metrics.add_score(score)

        self.current_total = metrics['total_students']
        self.current_attentive = metrics['attentive']
        self.current_distracted = metrics['distracted']

        # Dakikalık takip için veri ekle
        self.minute_tracker.add_data(score, self.current_attentive, self.current_distracted)

        # Her dakika veritabanına kaydet
        if self.session_start and self.last_minute_save:
            elapsed = (datetime.now() - self.last_minute_save).total_seconds()
            if elapsed >= 60:
                self._save_minute_data()
                self.last_minute_save = datetime.now()

        if len(self.session_data) < 10000:
            self.session_data.append({
                "frame": self.metrics.frame_count,
                "score": score,
                "attentive": self.current_attentive,
                "distracted": self.current_distracted,
                "timestamp": (datetime.now() - self.session_start).total_seconds() if self.session_start else 0,
            })

        if self.current_total > 0:
            distracted_pct = (self.current_distracted / self.current_total) * 100
            if distracted_pct >= self.alert_pct and not self.is_snoozed:
                self.warn_label.setText(
                    f"⚠ {self.current_distracted} of {self.current_total} students distracted "
                    f"({distracted_pct:.0f}%) — please re-engage"
                )
                self.warn_label.setStyleSheet("color: #a32020; font-size: 11pt;")
                self.banner.setVisible(True)
                self.alert_timer.start(int(self.alert_display_seconds * 1000))

    def _update_ui(self):
        """Update UI elements."""
        self._update_all_labels()

    def _update_all_labels(self):
        """Update all metric labels."""
        self.score_label.setText(f"{int(self.metrics.rolling_avg())}")
        self.card_avg.value_label.setText(f"{self.metrics.rolling_avg():.1f}")
        self.card_peak.value_label.setText(f"{int(self.metrics.peak())}")
        self.card_distr_pct.value_label.setText(f"{self.metrics.distraction_pct():.1f}%")

        self.card_students_att.value_label.setText(f"{self.current_attentive}")
        self.card_students_dist.value_label.setText(f"{self.current_distracted}")

        if self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            minutes, seconds = divmod(int(elapsed), 60)
            hours, minutes = divmod(minutes, 60)
            self.time_badge.setText(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def closeEvent(self, event):
        """Uygulama kapatılırken veritabanını temizle."""
        self.on_stop()
        self.db.close()
        event.accept()