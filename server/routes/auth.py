from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from server import db
from server.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Kullanıcı adı zaten mevcut'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email zaten kayıtlı'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        full_name=data['full_name']
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Kayıt başarılı', 'user': user.to_dict()}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({'message': 'Giriş başarılı', 'user': user.to_dict()}), 200

    return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Çıkış başarılı'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'user': current_user.to_dict()}), 200

