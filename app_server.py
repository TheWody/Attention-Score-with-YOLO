from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt
from functools import wraps

app = Flask(__name__, template_folder='server/templates')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attention_monitor.db'
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Admin(db.Model):
    __tablename__ = 'admins'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            token = token.split()[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            if not data.get('is_admin'):
                return jsonify({'message': 'Admin access required!'}), 403
            current_admin = Admin.query.get(data['admin_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_admin, *args, **kwargs)

    return decorated

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

@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    data = request.get_json()

    if Admin.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(data['password'])
    new_admin = Admin(
        username=data['username'],
        password_hash=hashed_password,
        name=data['name']
    )

    db.session.add(new_admin)
    db.session.commit()

    return jsonify({'message': 'Admin registered successfully'}), 201

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    admin = Admin.query.filter_by(username=data['username']).first()

    if not admin or not check_password_hash(admin.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    from datetime import timedelta

    token = jwt.encode({
        'admin_id': admin.admin_id,
        'is_admin': True,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'token': token,
        'admin': {
            'admin_id': admin.admin_id,
            'username': admin.username,
            'name': admin.name
        }
    })

@app.route('/api/admin/teachers', methods=['GET'])
@admin_token_required
def get_all_teachers(current_admin):
    teachers = Teacher.query.all()
    return jsonify([{
        'teacher_id': t.teacher_id,
        'name': t.name,
        'email': t.email,
        'department': t.department,
        'total_courses': len(t.courses),
        'total_sessions': len(t.sessions)
    } for t in teachers])

@app.route('/api/admin/courses', methods=['GET'])
@admin_token_required
def get_all_courses(current_admin):
    courses = Course.query.all()
    return jsonify([{
        'course_id': c.course_id,
        'course_code': c.course_code,
        'course_name': c.course_name,
        'teacher_name': c.teacher.name if c.teacher else None,
        'classroom_location': c.classroom_location,
        'semester': c.semester,
        'total_sessions': len(c.sessions)
    } for c in courses])

@app.route('/api/admin/sessions', methods=['GET'])
@admin_token_required
def get_all_sessions(current_admin):
    teacher_id = request.args.get('teacher_id', type=int)
    course_id = request.args.get('course_id', type=int)
    status = request.args.get('status')

    query = Session.query

    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    if status:
        query = query.filter_by(status=status)

    sessions = query.order_by(Session.start_time.desc()).all()

    return jsonify([{
        'session_id': s.session_id,
        'course': {
            'course_code': s.course.course_code,
            'course_name': s.course.course_name
        },
        'teacher': {
            'teacher_id': s.teacher.teacher_id,
            'name': s.teacher.name
        },
        'start_time': s.start_time.isoformat() if s.start_time else None,
        'end_time': s.end_time.isoformat() if s.end_time else None,
        'duration_seconds': s.duration_seconds,
        'avg_attention_score': float(s.avg_attention_score) if s.avg_attention_score else None,
        'peak_score': s.peak_score,
        'total_students': s.total_students,
        'status': s.status
    } for s in sessions])

@app.route('/api/admin/stats', methods=['GET'])
@admin_token_required
def get_admin_stats(current_admin):
    total_teachers = Teacher.query.count()
    total_courses = Course.query.count()
    total_sessions = Session.query.filter_by(status='completed').count()
    active_sessions = Session.query.filter_by(status='active').count()

    avg_score = db.session.query(
        db.func.avg(Session.avg_attention_score)
    ).filter_by(status='completed').scalar()

    today = datetime.utcnow().date()
    today_sessions = Session.query.filter(
        db.func.date(Session.start_time) == today
    ).count()

    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_avg = db.session.query(
        db.func.avg(Session.avg_attention_score)
    ).filter(
        Session.status == 'completed',
        Session.start_time >= week_ago
    ).scalar()

    return jsonify({
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'overall_avg_score': float(avg_score) if avg_score else 0,
        'today_sessions': today_sessions,
        'week_avg_score': float(week_avg) if week_avg else 0
    })

@app.route('/api/admin/sessions/<int:session_id>', methods=['GET'])
@admin_token_required
def get_admin_session_detail(current_admin, session_id):
    session = Session.query.get(session_id)

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
            'teacher': {
                'teacher_id': session.teacher.teacher_id,
                'name': session.teacher.name,
                'department': session.teacher.department
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

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

def create_default_admin():
    """Varsayılan admin hesabı oluştur (eğer hiç admin yoksa)"""
    if Admin.query.count() == 0:
        default_admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            name='Sistem Yöneticisi'
        )
        db.session.add(default_admin)
        db.session.commit()
        print("=" * 50)
        print("🔐 VARSAYILAN ADMIN HESABI OLUŞTURULDU!")
        print("   Kullanıcı Adı: admin")
        print("   Şifre: admin123")
        print("   ⚠️  Güvenlik için şifreyi değiştirin!")
        print("=" * 50)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(host='0.0.0.0', port=5001, debug=True)