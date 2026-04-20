import sys
import cv2
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer

from config import *
from core.camera_handler import CameraHandler
from core.gesture_detector import GestureDetector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Core components
        self.camera = CameraHandler()
        self.gesture_detector = GestureDetector()
        self.camera.start()
        
        # UI
        self.setWindowTitle("GestureInterface - Phase 1")
        self.setGeometry(0, 0, CAMERA_WIDTH, CAMERA_HEIGHT)
        self.setStyleSheet("background-color: black;")
        
        self.camera_label = QLabel()
        self.setCentralWidget(self.camera_label)
        
        # Timer de rendu
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / REFRESH_RATE))
    
    def update_frame(self):
        frame = self.camera.get_frame()
        if frame is None:
            return
        
        # Détection des mains
        results = self.gesture_detector.detect(frame)
        frame = self.gesture_detector.draw_hands(frame, results)
        
        # Extrait les positions
        hands = self.gesture_detector.get_hand_positions(
            results, CAMERA_WIDTH, CAMERA_HEIGHT
        )
        
        # Affiche le nombre de mains détectées
        if hands:
            cv2.putText(frame, f"Mains détectées: {len(hands)}", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Convertir et afficher
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, 
                         QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.camera_label.setPixmap(pixmap)
    
    def closeEvent(self, event):
        self.camera.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()