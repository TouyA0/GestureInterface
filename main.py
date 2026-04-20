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
        self.showFullScreen()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / REFRESH_RATE))

    def _crop_black_bars(self, frame, threshold=10):
        """Rogne les bandes noires (pillarbox/letterbox) ajoutées par la source vidéo."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        col_nonblack = np.where(gray.max(axis=0) > threshold)[0]
        row_nonblack = np.where(gray.max(axis=1) > threshold)[0]
        if len(col_nonblack) == 0 or len(row_nonblack) == 0:
            return frame
        return frame[row_nonblack[0]:row_nonblack[-1] + 1,
                     col_nonblack[0]:col_nonblack[-1] + 1]

    def update_frame(self):
        frame = self.camera.get_frame()
        if frame is None:
            return

        frame = self._crop_black_bars(frame)

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

        # Cover : resize pour remplir exactement le widget sans bande noire
        win_w, win_h = self.width(), self.height()
        if win_w <= 0 or win_h <= 0:
            return
        fh, fw = frame.shape[:2]
        scale = max(win_w / fw, win_h / fh)
        sw, sh = int(fw * scale), int(fh * scale)
        scaled = cv2.resize(frame, (sw, sh), interpolation=cv2.INTER_LINEAR)
        x0 = (sw - win_w) // 2
        y0 = (sh - win_h) // 2
        cover = scaled[y0:y0 + win_h, x0:x0 + win_w]

        rgb = np.ascontiguousarray(cv2.cvtColor(cover, cv2.COLOR_BGR2RGB))
        self._pixmap = QPixmap.fromImage(
            QImage(rgb.data, win_w, win_h, win_w * 3, QImage.Format.Format_RGB888)
        )
        self._rgb_keep = rgb  # garde une référence au buffer
        self.update()

    def paintEvent(self, event):
        if self._pixmap is None:
            return
        QPainter(self).drawPixmap(0, 0, self._pixmap)

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
