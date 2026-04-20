import pygetwindow as gw
import pyautogui
import time

class WindowController:
    """Contrôle les fenêtres Windows avec gestes"""
    
    def __init__(self):
        self.dragging_window = None
        self.drag_start_pos = None
        self.last_cursor_pos = None
    
    def get_window_at_position(self, x, y):
        """Retourne la fenêtre sous la position (x, y)"""
        try:
            windows = gw.getWindowsAt(x, y)
            if windows:
                # Retourne la fenêtre au-dessus
                return windows[-1]
        except:
            pass
        return None
    
    def start_drag(self, x, y):
        """Lance le drag d'une fenêtre à la position (x, y)"""
        window = self.get_window_at_position(x, y)
        if window:
            self.dragging_window = window
            self.drag_start_pos = (x, y)
            self.last_cursor_pos = (x, y)
            
            # Simule un clic à la position
            pyautogui.mouseDown(x, y)
            return True
        return False
    
    def drag_window(self, x, y):
        """Déplace la fenêtre en cours de drag"""
        if not self.dragging_window or not self.drag_start_pos:
            return False
        
        try:
            # Simule le mouvement de la souris
            pyautogui.moveTo(x, y, duration=0.01)
            self.last_cursor_pos = (x, y)
            return True
        except:
            return False
    
    def stop_drag(self):
        """Arrête le drag"""
        if self.dragging_window:
            pyautogui.mouseUp()
        
        self.dragging_window = None
        self.drag_start_pos = None
        self.last_cursor_pos = None
    
    def list_windows(self):
        """Liste toutes les fenêtres ouvertes"""
        try:
            windows = gw.getAllWindows()
            return [w for w in windows if w.title.strip()]  # Exclut les fenêtres sans titre
        except:
            return []