import sqlite3
from datetime import datetime
from pathlib import Path
import json

class DatabaseManager:

    def __init__(self, db_path=None):
        if db_path is None:
            save_dir = Path.home() / "AttentionMonitor_Data"
            save_dir.mkdir(exist_ok=True)
            db_path = save_dir / "attention_monitor.db"

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
        print(f"Veritabanı başlatıldı: {db_path}")

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds REAL,
                avg_attention_score REAL,
                peak_score INTEGER,
                total_students INTEGER,
                total_frames INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            CREATE TABLE IF NOT EXISTS minute_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                minute_number INTEGER NOT NULL,
                avg_score REAL NOT NULL,
                min_score INTEGER,
                max_score INTEGER,
                avg_attentive INTEGER,
                avg_distracted INTEGER,
                total_frames INTEGER,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
            INSERT INTO sessions (course_name, start_time)
            VALUES (?, ?)
            INSERT INTO minute_metrics
            (session_id, minute_number, avg_score, min_score, max_score,
             avg_attentive, avg_distracted, total_frames, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            SELECT start_time FROM sessions WHERE session_id = ?
            UPDATE sessions
            SET end_time = ?,
                duration_seconds = ?,
                avg_attention_score = ?,
                peak_score = ?,
                total_students = ?,
                total_frames = ?
            WHERE session_id = ?
            SELECT session_id, course_name, start_time, end_time,
                   duration_seconds, avg_attention_score, peak_score,
                   total_students, total_frames
            FROM sessions
            WHERE session_id = ?
            SELECT minute_number, avg_score, min_score, max_score,
                   avg_attentive, avg_distracted, total_frames, timestamp
            FROM minute_metrics
            WHERE session_id = ?
            ORDER BY minute_number
            SELECT session_id, course_name, start_time, end_time,
                   duration_seconds, avg_attention_score, peak_score
            FROM sessions
            ORDER BY start_time DESC