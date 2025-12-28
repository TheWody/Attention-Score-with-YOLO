from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from server import db
from server.models.class_session import ClassSession, AttentionRecord

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    # Öğretmenin tüm dersleri
    total_classes = ClassSession.query.filter_by(teacher_id=current_user.id).count()
    active_classes = ClassSession.query.filter_by(teacher_id=current_user.id, is_active=True).count()
    completed_classes = ClassSession.query.filter_by(teacher_id=current_user.id, is_active=False).count()

    # Ortalama dikkat skoru
    avg_attention = db.session.query(func.avg(AttentionRecord.attention_score))\
        .join(ClassSession)\
        .filter(ClassSession.teacher_id == current_user.id)\
        .scalar() or 0

    # Son 5 ders
    recent_classes = ClassSession.query\
        .filter_by(teacher_id=current_user.id)\
        .order_by(ClassSession.start_time.desc())\
        .limit(5)\
        .all()

    return jsonify({
        'stats': {
            'total_classes': total_classes,
            'active_classes': active_classes,
            'completed_classes': completed_classes,
            'average_attention_score': round(avg_attention, 2)
        },
        'recent_classes': [c.to_dict() for c in recent_classes]
    }), 200

@dashboard_bp.route('/class/<int:class_id>/timeline', methods=['GET'])
@login_required
def get_class_timeline(class_id):
    class_session = ClassSession.query.get_or_404(class_id)

    if class_session.teacher_id != current_user.id:
        return jsonify({'error': 'Yetkisiz erişim'}), 403

    records = AttentionRecord.query\
        .filter_by(class_session_id=class_id)\
        .order_by(AttentionRecord.timestamp)\
        .all()

    timeline_data = [{
        'timestamp': r.timestamp.isoformat(),
        'attention_score': r.attention_score,
        'student_count': r.student_count
    } for r in records]

    return jsonify({
        'class': class_session.to_dict(),
        'timeline': timeline_data
    }), 200

