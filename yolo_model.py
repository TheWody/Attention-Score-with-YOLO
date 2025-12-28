from ultralytics import YOLO

class YOLOModel:

    def __init__(self, pose_model_path='yolov8n-pose.pt', emotion_model_path='yolov8n-emotion.pt'):

        self.pose_model = YOLO(pose_model_path)
        print(f"YOLOv8 Pose modeli ({pose_model_path}) yüklendi.")

        try:
            self.emotion_model = YOLO(emotion_model_path)
            print(f"YOLOv8 Emotion modeli ({emotion_model_path}) yüklendi.")
            self.emotion_labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        except Exception:

            print("Kullanıcı Duygu Modeli bulunamadı. Test amaçlı 'yolov8n-cls.pt' yükleniyor.")
            try:
                self.emotion_model = YOLO('yolov8n-cls.pt')
                self.emotion_labels = ["happy", "neutral", "sad", "surprise", "angry", "fear", "disgust"] * 200
            except Exception as e:
                print(f"Hata: Önceden eğitilmiş model bile yüklenemedi. ({e})")
                self.emotion_model = None

    def detect_pose(self, frame):
        results = self.pose_model(frame, conf=0.5, stream=True)
        return results

    def detect_emotion(self, face_frame):
        if self.emotion_model is None or face_frame is None or face_frame.size == 0:
            return "neutral"

        if face_frame.shape[0] < 32 or face_frame.shape[1] < 32:
            return "neutral"

        results = self.emotion_model(face_frame, conf=0.7, verbose=False)

        if not results:
            return "neutral"

        r = results[0]

        if hasattr(r, 'probs') and r.probs is not None:
            top_class_index = r.probs.top1

            if top_class_index < len(self.emotion_labels):
                return self.emotion_labels[top_class_index]

        return "neutral"

    def extract_and_analyze(self, results, frame):
        student_data = []
        for r in results:
            if r.keypoints is not None and r.keypoints.cpu().numpy() is not None:
                keypoints_xy = r.keypoints.xy.cpu().numpy()
                boxes = r.boxes.xyxy.cpu().numpy()

                for i in range(len(keypoints_xy)):
                    bbox = boxes[i]
                    x_min, y_min, x_max, y_max = map(int, bbox)

                    face_crop = frame[y_min:y_max, x_min:x_max]

                    emotion_label = "neutral"
                    if face_crop.size > 0:
                        emotion_label = self.detect_emotion(face_crop)

                    student_data.append({
                        'keypoints': keypoints_xy[i],
                        'bbox': bbox,
                        'emotion_label': emotion_label
                    })
        return student_data