import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer

from config import *
from core.camera_handler import CameraHandler
from core.gesture_detector import GestureDetector
from core.gesture_processor import GestureProcessor

from core.gesture_processor import GestureProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Core components
        self.camera = CameraHandler()
        self.gesture_detector = GestureDetector()
        self.gesture_processor = GestureProcessor()
        self.camera.start()
        
        # UI
        self.setWindowTitle("GestureInterface - Phase 1 - Jour 3-4")
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
        
        # Traite les gestes
        commands = self.gesture_processor.process(hands)
        
        if hands:
            hand = hands[0]
            all_pts = hand['all_points']
            frame_h, frame_w = frame.shape[:2]

            # Convertis index et thumb en pixels aussi
            index_norm_x, index_norm_y = hand['index']
            index_pos = (int(index_norm_x * frame_w), int(index_norm_y * frame_h))

            thumb_norm_x, thumb_norm_y = hand['thumb']
            thumb_pos = (int(thumb_norm_x * frame_w), int(thumb_norm_y * frame_h))
            
            # Affiche aussi le point 8 en GROS ROUGE
            cv2.circle(frame, index_pos, 20, (0, 0, 255), 3)
            cv2.putText(frame, "POINT 8", (index_pos[0]+30, index_pos[1]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Affiche un GROS cercle vert directement sur l'index
            cv2.circle(frame, index_pos, 15, (0, 255, 0), 2)
            cv2.circle(frame, index_pos, 3, (0, 255, 0), -1)
            cv2.putText(frame, "INDEX", (index_pos[0]+20, index_pos[1]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Affiche le pouce en rouge
            cv2.circle(frame, thumb_pos, 12, (0, 0, 255), 2)
            cv2.putText(frame, "THUMB", (thumb_pos[0]+20, thumb_pos[1]), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Calcule la distance pouce-index
            dist = np.sqrt((thumb_pos[0] - index_pos[0])**2 + 
                        (thumb_pos[1] - index_pos[1])**2)
            
            # Affiche la distance
            cv2.putText(frame, f"Distance: {int(dist)}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Détecte le pinch
            if dist < 40:
                cv2.putText(frame, "PINCH DETECTED!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.rectangle(frame, 
                            (index_pos[0]-30, index_pos[1]-30),
                            (index_pos[0]+30, index_pos[1]+30),
                            (0, 0, 255), 2)
        
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