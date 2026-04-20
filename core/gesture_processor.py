import numpy as np
from config import *

class GestureProcessor:
    """Traite les gestes et génère des commandes"""
    
    def __init__(self):
        self.prev_positions = {}
        self.smoothing_factor = GESTURE_SMOOTHING
        self.cursor_pos = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2)
        
    def process(self, hands_data):
        """Traite les données des mains et retourne les commandes"""
        commands = {
            'cursor': self.cursor_pos,
            'pinch': False,
            'swipe': None,
            'hands_count': len(hands_data)
        }
        
        if not hands_data:
            return commands
        
        # Traiter la première main détectée
        hand = hands_data[0]
        
        # Curseur = position de l'index
        raw_cursor = hand['index']
        self.cursor_pos = self._smooth_position(self.cursor_pos, raw_cursor)
        commands['cursor'] = self.cursor_pos
        
        # Détecte pinch
        dist = np.sqrt((hand['thumb'][0] - hand['index'][0])**2 + 
                    (hand['thumb'][1] - hand['index'][1])**2)
        commands['pinch'] = dist < (PINCH_THRESHOLD * CAMERA_WIDTH)
        
        return commands
    
    def _smooth_position(self, prev, curr):
        """Lisse les mouvements pour éviter les tremblements"""
        return (
            int(prev[0] * self.smoothing_factor + curr[0] * (1 - self.smoothing_factor)),
            int(prev[1] * self.smoothing_factor + curr[1] * (1 - self.smoothing_factor))
        )