import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtCore import QTimer, Qt

from config import *
from core.camera_handler import CameraHandler
from core.gesture_detector import GestureDetector


class GestureApp(QWidget):
    def __init__(self):
        super().__init__()
        self._pixmap = None

        self.camera = CameraHandler()
        self.gesture_detector = GestureDetector()
        self.camera.start()

        self.setWindowTitle("GestureInterface")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        screen_geom = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geom)
        self.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / REFRESH_RATE))

    def update_frame(self):
        frame = self.camera.get_frame()
        if frame is None:
            return

        results = self.gesture_detector.detect(frame)
        frame = self.gesture_detector.draw_hands(frame, results)

        hands = self.gesture_detector.get_hand_positions(results, CAMERA_WIDTH, CAMERA_HEIGHT)

        if hands:
            hand = hands[0]
            fh, fw = frame.shape[:2]

            ix, iy = hand['index']
            index_pos = (int(ix * fw), int(iy * fh))
            cv2.circle(frame, index_pos, 15, (0, 255, 0), 2)

            tx, ty = hand['thumb']
            thumb_pos = (int(tx * fw), int(ty * fh))
            cv2.circle(frame, thumb_pos, 12, (0, 0, 255), 2)

            dist = np.hypot(index_pos[0] - thumb_pos[0], index_pos[1] - thumb_pos[1])
            cv2.putText(frame, f"Distance: {int(dist)}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            if dist < 40:
                cv2.putText(frame, "PINCH!", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        fh, fw = frame.shape[:2]
        rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        self._pixmap = QPixmap.fromImage(
            QImage(rgb.data, fw, fh, fw * 3, QImage.Format.Format_RGB888)
        )
        self.update()

    def paintEvent(self, event):
        if self._pixmap is None:
            return
        QPainter(self).drawPixmap(self.rect(), self._pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.camera.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = GestureApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
