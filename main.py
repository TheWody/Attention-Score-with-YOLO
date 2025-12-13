# Tüm sınıfları içe aktar
from camera_manager import CameraFeedManager
from yolo_model import YOLOModel
from attention_analyzer import AttentionAnalyzer
import cv2


class GUIApplication:
    """Tüm proje bileşenlerini birleştirerek ana akışı yönetir ve gösterir."""

    def __init__(self):
        print("Sistem bileşenleri başlatılıyor...")
        self.camera = CameraFeedManager(source=0)
        self.yolo = YOLOModel()
        self.analyzer = AttentionAnalyzer()
        self.last_attention_data = []

    def draw_annotations(self, frame, student_data):
        """Kare üzerine sınırlayıcı kutu, anahtar noktalar ve dikkat skorunu çizer."""
        for data in student_data:
            bbox = data['bbox']
            score = data['score']
            pose_state = data['pose_state']
            emotion_label = data['emotion_label']

            color = (0, 0, 255) if score < 70 else (0, 255, 0)
            x_min, y_min, x_max, y_max = map(int, bbox)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)

            text_score = f"Score: {score} ({pose_state})"

            text_emotion = f"Emotion: {emotion_label.upper()}"

            cv2.putText(frame, text_score, (x_min, y_min - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            cv2.putText(frame, text_emotion, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame

    def run(self):
        """Uygulamanın ana döngüsü."""
        if not self.camera.is_running:
            return

        while True:
            success, frame = self.camera.read_frame()
            if not success:
                break

            results = self.yolo.detect_pose(frame)
            student_data = self.yolo.extract_and_analyze(results, frame)

            processed_data = []

            for data in student_data:
                pose_state = self.analyzer.analyze_head_pose(data['keypoints'])
                emotion_label = data['emotion_label']

                score = self.analyzer.calculate_attention_score(pose_state, emotion_label)

                data['pose_state'] = pose_state
                data['score'] = score
                processed_data.append(data)

            annotated_frame = self.draw_annotations(frame, processed_data)

            cv2.imshow("Real-Time Attention Detector (Press 'q' to exit)", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.camera.release()
        print("Uygulama başarıyla sonlandırıldı.")


if __name__ == "__main__":
    app = GUIApplication()
    app.run()