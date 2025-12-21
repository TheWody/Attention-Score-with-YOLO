from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt
from functools import wraps
import os

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attention_monitor.db'
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Models
class Teacher(db.Model):
    __tablename__ = 'teachers'
    teacher_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100))
    courses = db.relationship('Course', backref='teacher', lazy=True)
    sessions = db.relationship('Session', backref='teacher', lazy=True)


class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'))
    classroom_location = db.Column(db.String(50))
    semester = db.Column(db.String(20))
    sessions = db.relationship('Session', backref='course', lazy=True)


class Session(db.Model):
    __tablename__ = 'sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    avg_attention_score = db.Column(db.Numeric(5, 2))
    peak_score = db.Column(db.Integer)
    total_students = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active')
    metrics = db.relationship('MinuteMetric', backref='session', lazy=True)


class MinuteMetric(db.Model):
    __tablename__ = 'minute_metrics'
    metric_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.session_id'))
    minute_number = db.Column(db.Integer, nullable=False)
    avg_score = db.Column(db.Numeric(5, 2), nullable=False)
    min_score = db.Column(db.Integer)
    max_score = db.Column(db.Integer)
    avg_attentive = db.Column(db.Integer)
    avg_distracted = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False)


# JWT Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            token = token.split()[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_teacher = Teacher.query.get(data['teacher_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_teacher, *args, **kwargs)

    return decorated


# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if Teacher.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    hashed_password = generate_password_hash(data['password'])
    new_teacher = Teacher(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_password,
        department=data.get('department', '')
    )

    db.session.add(new_teacher)
    db.session.commit()

    return jsonify({'message': 'Teacher registered successfully'}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    teacher = Teacher.query.filter_by(email=data['email']).first()

    if not teacher or not check_password_hash(teacher.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    from datetime import datetime, timedelta

    token = jwt.encode({
        'teacher_id': teacher.teacher_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'token': token,
        'teacher': {
            'teacher_id': teacher.teacher_id,
            'name': teacher.name,
            'email': teacher.email,
            'department': teacher.department
        }
    })


# Course Routes
@app.route('/api/courses', methods=['GET'])
@token_required
def get_courses(current_teacher):
    courses = Course.query.filter_by(teacher_id=current_teacher.teacher_id).all()
    return jsonify([{
        'course_id': c.course_id,
        'course_code': c.course_code,
        'course_name': c.course_name,
        'classroom_location': c.classroom_location,
        'semester': c.semester
    } for c in courses])


@app.route('/api/courses', methods=['POST'])
@token_required
def create_course(current_teacher):
    data = request.get_json()
    new_course = Course(
        course_code=data['course_code'],
        course_name=data['course_name'],
        teacher_id=current_teacher.teacher_id,
        classroom_location=data.get('classroom_location', ''),
        semester=data.get('semester', '')
    )

    db.session.add(new_course)
    db.session.commit()

    return jsonify({'message': 'Course created', 'course_id': new_course.course_id}), 201


# Session Routes
@app.route('/api/sessions/start', methods=['POST'])
@token_required
def start_session(current_teacher):
    data = request.get_json()

    new_session = Session(
        course_id=data['course_id'],
        teacher_id=current_teacher.teacher_id,
        start_time=datetime.utcnow(),
        status='active'
    )

    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        'message': 'Session started',
        'session_id': new_session.session_id
    }), 201


@app.route('/api/sessions/<int:session_id>/minute', methods=['POST'])
@token_required
def save_minute_metric(current_teacher, session_id):
    data = request.get_json()

    # Verify session belongs to teacher
    session = Session.query.filter_by(
        session_id=session_id,
        teacher_id=current_teacher.teacher_id
    ).first()

    if not session:
        return jsonify({'message': 'Session not found'}), 404

    metric = MinuteMetric(
        session_id=session_id,
        minute_number=data['minute_number'],
        avg_score=data['avg_score'],
        min_score=data['min_score'],
        max_score=data['max_score'],
        avg_attentive=data['avg_attentive'],
        avg_distracted=data['avg_distracted'],
        timestamp=datetime.utcnow()
    )

    db.session.add(metric)
    db.session.commit()

    return jsonify({'message': 'Minute metric saved'}), 201


@app.route('/api/sessions/<int:session_id>/end', methods=['POST'])
@token_required
def end_session(current_teacher, session_id):
    data = request.get_json()

    session = Session.query.filter_by(
        session_id=session_id,
        teacher_id=current_teacher.teacher_id
    ).first()

    if not session:
        return jsonify({'message': 'Session not found'}), 404

    session.end_time = datetime.utcnow()
    session.duration_seconds = data['duration_seconds']
    session.avg_attention_score = data['avg_attention_score']
    session.peak_score = data['peak_score']
    session.total_students = data['total_students']
    session.status = 'completed'

    db.session.commit()

    return jsonify({
        'message': 'Session completed',
        'avg_attention_score': float(session.avg_attention_score)
    })


@app.route('/api/sessions', methods=['GET'])
@token_required
def get_sessions(current_teacher):
    course_id = request.args.get('course_id', type=int)

    query = Session.query.filter_by(teacher_id=current_teacher.teacher_id)
    if course_id:
        query = query.filter_by(course_id=course_id)

    sessions = query.order_by(Session.start_time.desc()).all()

    return jsonify([{
        'session_id': s.session_id,
        'course': {
            'course_code': s.course.course_code,
            'course_name': s.course.course_name
        },
        'start_time': s.start_time.isoformat() if s.start_time else None,
        'end_time': s.end_time.isoformat() if s.end_time else None,
        'duration_seconds': s.duration_seconds,
        'avg_attention_score': float(s.avg_attention_score) if s.avg_attention_score else None,
        'peak_score': s.peak_score,
        'total_students': s.total_students,
        'status': s.status
    } for s in sessions])


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
@token_required
def get_session_detail(current_teacher, session_id):
    session = Session.query.filter_by(
        session_id=session_id,
        teacher_id=current_teacher.teacher_id
    ).first()

    if not session:
        return jsonify({'message': 'Session not found'}), 404

    metrics = MinuteMetric.query.filter_by(session_id=session_id).order_by(MinuteMetric.minute_number).all()

    return jsonify({
        'session': {
            'session_id': session.session_id,
            'course': {
                'course_code': session.course.course_code,
                'course_name': session.course.course_name,
                'classroom_location': session.course.classroom_location
            },
            'start_time': session.start_time.isoformat() if session.start_time else None,
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration_seconds': session.duration_seconds,
            'avg_attention_score': float(session.avg_attention_score) if session.avg_attention_score else None,
            'peak_score': session.peak_score,
            'total_students': session.total_students,
            'status': session.status
        },
        'minute_metrics': [{
            'minute': m.minute_number,
            'avg_score': float(m.avg_score),
            'min_score': m.min_score,
            'max_score': m.max_score,
            'avg_attentive': m.avg_attentive,
            'avg_distracted': m.avg_distracted,
            'timestamp': m.timestamp.isoformat()
        } for m in metrics]
    })


# Dashboard Statistics
@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_teacher):
    total_sessions = Session.query.filter_by(
        teacher_id=current_teacher.teacher_id,
        status='completed'
    ).count()

    avg_scores = db.session.query(
        db.func.avg(Session.avg_attention_score)
    ).filter_by(
        teacher_id=current_teacher.teacher_id,
        status='completed'
    ).scalar()

    active_sessions = Session.query.filter_by(
        teacher_id=current_teacher.teacher_id,
        status='active'
    ).count()

    return jsonify({
        'total_sessions': total_sessions,
        'average_attention_score': float(avg_scores) if avg_scores else 0,
        'active_sessions': active_sessions
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)