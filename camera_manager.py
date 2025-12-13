import cv2


class CameraFeedManager:
    """Kamera girişini yönetir ve kareleri (frame) sağlar."""

    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            print(f"Hata: Kamera kaynağı {source} açılamadı.")
            self.is_running = False
        else:
            self.is_running = True

    def read_frame(self):
        """Kameradan bir kare okur."""
        if self.is_running:
            success, frame = self.cap.read()
            return success, frame
        return False, None

    def release(self):
        """Kamera kaynağını serbest bırakır."""
        if self.is_running:
            self.cap.release()
            cv2.destroyAllWindows()
            print("Kamera serbest bırakıldı.")
