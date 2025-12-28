import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///attention_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'models/yolo_fer_finetuned.pt')

    SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.getenv('SERVER_PORT', 5000))

    ATTENTION_EMOTIONS = {
        'happy': 0.8,
        'neutral': 0.7,
        'surprise': 0.6,
        'sad': 0.3,
        'angry': 0.2,
        'fear': 0.2,
        'disgust': 0.1
    }
