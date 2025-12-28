import numpy as np
from config import Config

class AttentionAnalyzer:
    def __init__(self):
        self.emotion_weights = Config.ATTENTION_EMOTIONS

    def calculate_attention_score(self, emotions_detected: dict) -> float:
        """
        Tespit edilen duygulara göre dikkat skoru hesaplar.

        Args:
            emotions_detected: {'happy': 3, 'neutral': 5, 'sad': 1, ...}

        Returns:
            0-100 arasında dikkat skoru
        """
        if not emotions_detected:
            return 0.0

        total_faces = sum(emotions_detected.values())
        if total_faces == 0:
            return 0.0

        weighted_sum = 0
        for emotion, count in emotions_detected.items():
            weight = self.emotion_weights.get(emotion.lower(), 0.5)
            weighted_sum += weight * count

        attention_score = (weighted_sum / total_faces) * 100
        return round(min(100, max(0, attention_score)), 2)

    def analyze_frame_emotions(self, detections: list) -> dict:
        """
        YOLO tespitlerinden duygu sayılarını çıkarır.

        Args:
            detections: YOLO model çıktısı

        Returns:
            {'happy': 3, 'neutral': 5, ...}
        """
        emotion_counts = {}

        for detection in detections:
            emotion = detection.get('emotion', 'neutral')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        return emotion_counts

