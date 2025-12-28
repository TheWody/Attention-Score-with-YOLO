import sqlite3
from datetime import datetime
from pathlib import Path
import json


class DatabaseManager:
    """SQLite veritabanı yöneticisi - attention score verilerini saklar."""

    def __init__(self, db_path=None):
        """Veritabanı bağlantısını başlatır."""
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
        """Gerekli tabloları oluşturur."""
        # Sessions tablosu - her kayıt oturumu için
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
        ''')

        # Minute_metrics tablosu - her dakika için metrikler
        self.cursor.execute('''
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
        ''')

        self.conn.commit()

    def start_session(self, course_name="Unknown Course"):
        """Yeni bir session başlatır ve session_id döndürür."""
        start_time = datetime.now().isoformat()

        self.cursor.execute('''
            INSERT INTO sessions (course_name, start_time)
            VALUES (?, ?)
        ''', (course_name, start_time))

        self.conn.commit()
        session_id = self.cursor.lastrowid
        print(f"Yeni session başlatıldı: ID={session_id}, Course={course_name}")
        return session_id

    def save_minute_metric(self, session_id, minute_number, avg_score,
                           min_score, max_score, avg_attentive,
                           avg_distracted, total_frames):
        """Bir dakikalık metriği kaydeder."""
        timestamp = datetime.now().isoformat()

        self.cursor.execute('''
            INSERT INTO minute_metrics 
            (session_id, minute_number, avg_score, min_score, max_score,
             avg_attentive, avg_distracted, total_frames, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, minute_number, avg_score, min_score, max_score,
              avg_attentive, avg_distracted, total_frames, timestamp))

        self.conn.commit()
        print(f"Dakika {minute_number} metriği kaydedildi - Avg Score: {avg_score:.1f}")

    def end_session(self, session_id, avg_attention_score, peak_score,
                    total_students, total_frames):
        """Session'ı sonlandırır ve özet bilgileri günceller."""
        end_time = datetime.now().isoformat()

        # Start time'ı al
        self.cursor.execute('''
            SELECT start_time FROM sessions WHERE session_id = ?
        ''', (session_id,))

        result = self.cursor.fetchone()
        if result:
            start_time = datetime.fromisoformat(result[0])
            duration = (datetime.now() - start_time).total_seconds()
        else:
            duration = 0

        # Session bilgilerini güncelle
        self.cursor.execute('''
            UPDATE sessions 
            SET end_time = ?,
                duration_seconds = ?,
                avg_attention_score = ?,
                peak_score = ?,
                total_students = ?,
                total_frames = ?
            WHERE session_id = ?
        ''', (end_time, duration, avg_attention_score, peak_score,
              total_students, total_frames, session_id))

        self.conn.commit()
        print(f"Session {session_id} sonlandırıldı - Ortalama Attention Score: {avg_attention_score:.1f}")
        return avg_attention_score

    def get_session_summary(self, session_id):
        """Belirli bir session'ın özet bilgilerini döndürür."""
        self.cursor.execute('''
            SELECT session_id, course_name, start_time, end_time,
                   duration_seconds, avg_attention_score, peak_score,
                   total_students, total_frames
            FROM sessions
            WHERE session_id = ?
        ''', (session_id,))

        result = self.cursor.fetchone()
        if result:
            return {
                'session_id': result[0],
                'course_name': result[1],
                'start_time': result[2],
                'end_time': result[3],
                'duration_seconds': result[4],
                'avg_attention_score': result[5],
                'peak_score': result[6],
                'total_students': result[7],
                'total_frames': result[8]
            }
        return None

    def get_minute_metrics(self, session_id):
        """Bir session'ın tüm dakikalık metriklerini döndürür."""
        self.cursor.execute('''
            SELECT minute_number, avg_score, min_score, max_score,
                   avg_attentive, avg_distracted, total_frames, timestamp
            FROM minute_metrics
            WHERE session_id = ?
            ORDER BY minute_number
        ''', (session_id,))

        results = self.cursor.fetchall()
        return [{
            'minute': row[0],
            'avg_score': row[1],
            'min_score': row[2],
            'max_score': row[3],
            'avg_attentive': row[4],
            'avg_distracted': row[5],
            'total_frames': row[6],
            'timestamp': row[7]
        } for row in results]

    def get_all_sessions(self):
        """Tüm session'ları listeler."""
        self.cursor.execute('''
            SELECT session_id, course_name, start_time, end_time,
                   duration_seconds, avg_attention_score, peak_score
            FROM sessions
            ORDER BY start_time DESC
        ''')

        results = self.cursor.fetchall()
        return [{
            'session_id': row[0],
            'course_name': row[1],
            'start_time': row[2],
            'end_time': row[3],
            'duration_seconds': row[4],
            'avg_attention_score': row[5],
            'peak_score': row[6]
        } for row in results]

    def export_session_to_json(self, session_id, filepath=None):
        """Bir session'ı JSON formatında export eder."""
        session = self.get_session_summary(session_id)
        if not session:
            print(f"Session {session_id} bulunamadı.")
            return None

        minutes = self.get_minute_metrics(session_id)

        export_data = {
            'session': session,
            'minute_metrics': minutes
        }

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = Path.home() / "AttentionMonitor_Data"
            filepath = save_dir / f"session_{session_id}_{timestamp}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"Session {session_id} export edildi: {filepath}")
        return filepath

    def close(self):
        """Veritabanı bağlantısını kapatır."""
        self.conn.close()
        print("Veritabanı bağlantısı kapatıldı.")