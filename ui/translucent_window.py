from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QFont
from config import *

class TranslucentWindow(QMainWindow):
    """Fenêtre translucide draggable"""
    
    def __init__(self, title="Fenêtre", width=400, height=300):
        super().__init__()
        
        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)
        
        # Rend la fenêtre translucide
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint)
        
        # Style
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: rgba(0, 20, 40, {int(WINDOW_OPACITY * 255)});
                border: 2px solid #00D4FF;
                border-radius: 10px;
            }}
            QLabel {{
                color: #00D4FF;
                font-family: 'Consolas';
                font-size: 12px;
                background-color: transparent;
            }}
        """)
        
        # Content
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QLabel(f"Contenu de {title}")
        self.label.setFont(QFont("Consolas", 11))
        self.layout.addWidget(self.label)
        
        # Pour drag-drop
        self.drag_start_pos = None
        self.is_being_dragged = False
    
    def mousePressEvent(self, event):
        """Détecte le début du drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.is_being_dragged = True
    
    def mouseMoveEvent(self, event):
        """Déplace la fenêtre pendant le drag"""
        if self.is_being_dragged and self.drag_start_pos:
            self.move(event.globalPosition().toPoint() - self.drag_start_pos)
    
    def mouseReleaseEvent(self, event):
        """Arrête le drag"""
        self.is_being_dragged = False
    
    def set_content(self, text):
        """Met à jour le contenu"""
        self.label.setText(text)