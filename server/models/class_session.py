from server import db
from datetime import datetime

class ClassSession(db.Model):
    __tablename__ = 'class_sessions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    attention_records = db.relationship('AttentionRecord', backref='class_session', lazy=True)

    @property
    def average_attention_score(self):
        if not self.attention_records:
            return 0.0
        total = sum(record.attention_score for record in self.attention_records)
        return round(total / len(self.attention_records), 2)

    @property
    def duration_minutes(self):
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.full_name if self.teacher else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active,
            'average_attention_score': self.average_attention_score,
            'duration_minutes': self.duration_minutes,
            'total_records': len(self.attention_records)
        }


class AttentionRecord(db.Model):
    __tablename__ = 'attention_records'

    id = db.Column(db.Integer, primary_key=True)
    class_session_id = db.Column(db.Integer, db.ForeignKey('class_sessions.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    attention_score = db.Column(db.Float, nullable=False)
    student_count = db.Column(db.Integer, default=0)
    emotions_detected = db.Column(db.JSON)  # {'happy': 3, 'neutral': 5, ...}

    def to_dict(self):
        return {
            'id': self.id,
            'class_session_id': self.class_session_id,
            'timestamp': self.timestamp.isoformat(),
            'attention_score': self.attention_score,
            'student_count': self.student_count,
            'emotions_detected': self.emotions_detected
        }

