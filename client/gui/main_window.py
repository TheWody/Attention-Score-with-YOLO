import cv2
import numpy as np
from datetime import datetime
from collections import deque

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QSizePolicy, QSpacerItem, QLineEdit, QMessageBox
)

from core import CameraFeedManager, YOLOModel, AttentionAnalyzer, generate_lesson_report
from client import APIClient


class VideoProcessingThread(QThread):
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
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 12px;
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

    def __init__(self, api_client: APIClient, course: dict, teacher: dict):
        super().__init__()
        self.api_client = api_client
        self.course = course
        self.teacher = teacher

        self.setWindowTitle(f"Classroom Monitor - {course['course_code']} ({teacher['name']})")
        self.resize(1200, 500)

        self.is_running = False
        self.metrics = MetricsTracker()
        self.video_thread = None
        self.session_start = None
        self.server_session_id = None

        self.minute_tracker = MinuteTracker()
        self.current_minute = 0
        self.last_minute_save = None
        self.minute_data_list = []

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
        left_card = QFrame()
        left_card.setStyleSheet("""
            QFrame {
                background: #e5e5e5;
                border-radius: 20px;
            }
        """)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(24, 20, 24, 20)
        left_layout.setSpacing(12)

        top_left_row = QHBoxLayout()

        course_text = f"{self.course['course_code']} - {self.course['course_name']}"
        self.course_label = QLabel(course_text)
        self.course_label.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 16pt;
                font-weight: 600;
                color: #222;
                border: 1px solid #dddddd;
            }
        """)
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

        subtitle = QLabel(f"Teacher: {self.teacher['name']} | {self.course.get('classroom_location', 'Classroom')}")
        subtitle.setStyleSheet('font-size: 13pt; color: #555;')
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
        self.view_label.setText("Camera will appear here\nClick 'Start' to begin monitoring")
        left_layout.addWidget(self.view_label)

        button_layout = self._create_control_buttons()
        left_layout.addLayout(button_layout)

        return left_card

    def _create_control_buttons(self):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_btn = QPushButton("Start Session")
        self.stop_btn = QPushButton("End Session")
        self.reset_btn = QPushButton("Reset")

        self.start_btn.setStyleSheet(
            "QPushButton { background: #29b566; color: white; "
            'border-radius: 18px; padding: 6px 20px; font-weight: 600; }'
        )
        self.stop_btn.setStyleSheet(
            "QPushButton { background: #e84545; color: white; "
            'border-radius: 18px; padding: 6px 20px; font-weight: 600; }'
        )
        self.reset_btn.setStyleSheet(
            'QPushButton { background: #ffffff; color: #222; '
            'border-radius: 18px; padding: 6px 18px; border: 1px solid #cfcfcf; }'
        )

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.reset_btn.clicked.connect(self.on_reset)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch(1)

        return button_layout

    def _create_right_panel(self):
        right_card = QFrame()
        right_card.setStyleSheet("""
            QFrame {
                background: #f0f0f0;
                border-radius: 20px;
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
        banner = QFrame()
        banner.setStyleSheet("QFrame { background: #ffe0df; border-radius: 14px; }")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(18, 10, 18, 10)
        banner_layout.setSpacing(16)

        self.warn_label = QLabel("⚠ Low attention detected")
        self.warn_label.setStyleSheet("color: #a32020; font-size: 11pt;")
        self.warn_label.setWordWrap(True)
        banner_layout.addWidget(self.warn_label, 1)

        self.ack_btn = QPushButton("Acknowledge")
        self.ack_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #222;
                border-radius: 18px;
                padding: 6px 18px;
                border: 1px solid #e0b3b2;
            }
        """)
        self.ack_btn.clicked.connect(self._on_acknowledge)
        banner_layout.addWidget(self.ack_btn)

        banner.setVisible(False)
        return banner

    def _cleanup_resources(self):
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
        if self.server_session_id is None:
            return

        summary = self.minute_tracker.get_summary()
        if summary is None:
            return

        self.minute_data_list.append({
            'minute_number': self.current_minute,
            'avg_score': summary['avg_score'],
            'min_score': summary['min_score'],
            'max_score': summary['max_score'],
            'avg_attentive': summary['avg_attentive'],
            'avg_distracted': summary['avg_distracted']
        })

        success = self.api_client.save_minute_metric(
            session_id=self.server_session_id,
            minute_number=self.current_minute,
            avg_score=summary['avg_score'],
            min_score=summary['min_score'],
            max_score=summary['max_score'],
            avg_attentive=summary['avg_attentive'],
            avg_distracted=summary['avg_distracted']
        )

        if success:
            self.current_minute += 1
            self.minute_tracker.reset()

    def on_start(self):
        if self.is_running:
            return

        self.server_session_id = self.api_client.start_session(self.course['course_id'])
        if not self.server_session_id:
            QMessageBox.critical(self, "Error", "Failed to start session on server")
            return

        self._cleanup_resources()
        self.is_running = True
        self.session_start = datetime.now()
        self.metrics.reset()
        self.start_btn.setEnabled(False)

        self.current_minute = 0
        self.minute_tracker.reset()
        self.last_minute_save = datetime.now()
        self.minute_data_list = []  # Rapor verilerini sıfırla

        self.video_thread = VideoProcessingThread()
        self.video_thread.frame_ready.connect(self._on_frame_ready)
        self.video_thread.fps_updated.connect(self._on_fps_updated)
        self.video_thread.metrics_updated.connect(self._on_metrics_updated)
        self.video_thread.start()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(100)

    def on_stop(self):
        if not self.is_running:
            return

        self.is_running = False

        if self.minute_tracker.frame_count > 0:
            self._save_minute_data()

        if self.server_session_id is not None:
            duration = (datetime.now() - self.session_start).total_seconds()
            final_avg = self.api_client.end_session(
                session_id=self.server_session_id,
                duration_seconds=int(duration),
                avg_attention_score=self.metrics.rolling_avg(),
                peak_score=int(self.metrics.peak()),
                total_students=self.current_total
            )

            if final_avg is not None:
                minutes = int(duration // 60)
                seconds = int(duration % 60)

                try:
                    report_path = generate_lesson_report(
                        minute_data=self.minute_data_list,
                        course_info=self.course,
                        teacher_name=self.teacher['name'],
                        duration_seconds=int(duration),
                        avg_attention_score=final_avg,
                        hypothesized_mean=60.0,
                        alpha=0.05,
                        open_browser=True
                    )
                    print(f"Report generated: {report_path}")
                except Exception as e:
                    print(f"Error generating report: {e}")

                msg = QMessageBox(self)
                msg.setWindowTitle("Session Completed")
                msg.setText(f"Session has been saved to server")
                msg.setInformativeText(
                    f"Course: {self.course['course_code']}\n"
                    f"Duration: {minutes} min {seconds} sec\n"
                    f"Average Attention Score: {final_avg:.1f}\n"
                    f"Peak Score: {int(self.metrics.peak())}\n"
                    f"Total Frames: {self.metrics.frame_count}\n\n"
                    f"📊 Detailed analysis report opened in browser!"
                )
                msg.setIcon(QMessageBox.Information)
                msg.exec_()

        self._cleanup_resources()
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        self.start_btn.setEnabled(True)
        self.view_label.setText("Session ended.\nClick 'Start Session' to begin new session")

    def on_reset(self):
        self.on_stop()
        self.metrics.reset()
        self.server_session_id = None
        self.current_minute = 0
        self.minute_tracker.reset()
        self.minute_data_list = []  # Rapor verilerini sıfırla
        self._update_all_labels()
        self.view_label.setText("Reset complete")
        self.banner.setVisible(False)

    def _on_acknowledge(self):
        self.is_snoozed = True
        self.banner.setVisible(False)
        if self.alert_timer.isActive():
            self.alert_timer.stop()
        self.snooze_timer.start(30000)

    def _on_snooze_end(self):
        self.is_snoozed = False

    def _on_alert_timeout(self):
        if not self.is_snoozed:
            self.banner.setVisible(False)

    def _on_frame_ready(self, frame, student_data):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = 3 * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaledToHeight(380, Qt.SmoothTransformation)
        self.view_label.setPixmap(scaled_pixmap)

    def _on_fps_updated(self, fps):
        self.card_fps.value_label.setText(f"{fps:.1f}")

    def _on_metrics_updated(self, metrics):
        score = metrics['avg_score']
        self.metrics.add_score(score)

        self.current_total = metrics['total_students']
        self.current_attentive = metrics['attentive']
        self.current_distracted = metrics['distracted']

        self.minute_tracker.add_data(score, self.current_attentive, self.current_distracted)

        if self.session_start and self.last_minute_save:
            elapsed = (datetime.now() - self.last_minute_save).total_seconds()
            if elapsed >= 60:
                self._save_minute_data()
                self.last_minute_save = datetime.now()

        if self.current_total > 0:
            distracted_pct = (self.current_distracted / self.current_total) * 100
            if distracted_pct >= self.alert_pct and not self.is_snoozed:
                self.warn_label.setText(
                    f"⚠ {self.current_distracted}/{self.current_total} students distracted ({distracted_pct:.0f}%)"
                )
                self.banner.setVisible(True)
                self.alert_timer.start(int(self.alert_display_seconds * 1000))

    def _update_ui(self):
        self._update_all_labels()

    def _update_all_labels(self):
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
        self.on_stop()