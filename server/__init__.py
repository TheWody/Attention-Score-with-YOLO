from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")

    login_manager.login_view = 'auth.login'

    from server.routes.auth import auth_bp
    from server.routes.classes import classes_bp
    from server.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(classes_bp, url_prefix='/api/classes')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    with app.app_context():
        db.create_all()

    return app

