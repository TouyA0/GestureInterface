import cv2
import numpy as np
import threading
from queue import Queue
from config import *

class CameraHandler:
    """Gère le flux caméra en temps réel"""
    
    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, CAMERA_BRIGHTNESS)
        
        self.frame_queue = Queue(maxsize=2)
        self.running = False
        self.thread = None
        
    def start(self):
        """Lance le thread de capture caméra"""
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Arrête la capture"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.cap.release()
        
    def _capture_loop(self):
        """Boucle de capture (tourne en arrière-plan)"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Mirror le flux (comme un miroir)
            frame = cv2.flip(frame, 1)
            
            # Mets à jour la queue (garde seulement la frame la plus récente)
            try:
                self.frame_queue.get_nowait()  # Vide l'ancienne frame
            except:
                pass
            self.frame_queue.put(frame)
    
    def get_frame(self):
        """Récupère la dernière frame"""
        try:
            return self.frame_queue.get_nowait()
        except:
            return None
    
    def get_resolution(self):
        """Retourne la résolution du flux"""
        return (CAMERA_WIDTH, CAMERA_HEIGHT)