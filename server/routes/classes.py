from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from server import db
from server.models.class_session import ClassSession, AttentionRecord

classes_bp = Blueprint('classes', __name__)

@classes_bp.route('/', methods=['GET'])
@login_required
def get_all_classes():
    classes = ClassSession.query.filter_by(teacher_id=current_user.id).all()
    return jsonify({'classes': [c.to_dict() for c in classes]}), 200

@classes_bp.route('/', methods=['POST'])
@login_required
def create_class():
    data = request.get_json()

    class_session = ClassSession(
        name=data['name'],
        description=data.get('description', ''),
        teacher_id=current_user.id
    )

    db.session.add(class_session)
    db.session.commit()

    return jsonify({'message': 'Ders oluşturuldu', 'class': class_session.to_dict()}), 201

@classes_bp.route('/<int:class_id>', methods=['GET'])
@login_required
def get_class(class_id):
    class_session = ClassSession.query.get_or_404(class_id)

    if class_session.teacher_id != current_user.id:
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    return jsonify({'class': class_session.to_dict()}), 200

@classes_bp.route('/<int:class_id>/end', methods=['POST'])
@login_required
def end_class(class_id):
    class_session = ClassSession.query.get_or_404(class_id)

    if class_session.teacher_id != current_user.id:
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    class_session.is_active = False
    class_session.end_time = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Ders sonlandırıldı', 'class': class_session.to_dict()}), 200

@classes_bp.route('/<int:class_id>/attention', methods=['POST'])
@login_required
def add_attention_record(class_id):
    class_session = ClassSession.query.get_or_404(class_id)

    if class_session.teacher_id != current_user.id:
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    data = request.get_json()

    record = AttentionRecord(
        class_session_id=class_id,
        attention_score=data['attention_score'],
        student_count=data.get('student_count', 0),
        emotions_detected=data.get('emotions_detected', {})
    )

    db.session.add(record)
    db.session.commit()

    return jsonify({'message': 'Kayıt eklendi', 'record': record.to_dict()}), 201

@classes_bp.route('/<int:class_id>/records', methods=['GET'])
@login_required
def get_attention_records(class_id):
    class_session = ClassSession.query.get_or_404(class_id)

    if class_session.teacher_id != current_user.id:
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    records = AttentionRecord.query.filter_by(class_session_id=class_id).all()
    return jsonify({'records': [r.to_dict() for r in records]}), 200

