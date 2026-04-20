import cv2
import mediapipe as mp
import numpy as np
from config import *

class GestureDetector:
    """Détecte les mains et les gestes"""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            min_detection_confidence=HAND_DETECTION_CONFIDENCE,
            min_tracking_confidence=HAND_TRACKING_CONFIDENCE
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
    def detect(self, frame):
        """Détecte les mains dans l'image"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        return results
    
    def draw_hands(self, frame, results):
        """Dessine les mains et les points sur l'image"""
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )
        return frame
    
    def get_hand_positions(self, results, frame_width, frame_height):
        """Extrait les positions des mains"""
        hands_data = []
        
        if not results.multi_hand_landmarks:
            return hands_data
        
        for hand_landmarks in results.multi_hand_landmarks:
            hand_dict = {}
            
            # Utilise directement les coordonnées NORMALISÉES (0-1)
            # sans les convertir en pixels
            for i, landmark in enumerate(hand_landmarks.landmark):
                # Stocke comme coordonnées normalisées
                hand_dict[i] = (landmark.x, landmark.y)
            
            hands_data.append({
                'thumb': hand_dict[4],
                'index': hand_dict[8],
                'middle': hand_dict[12],
                'ring': hand_dict[16],
                'pinky': hand_dict[20],
                'palm': hand_dict[0],
                'all_points': hand_dict
            })
        
        return hands_data
    
    def distance(self, p1, p2):
        """Calcule la distance entre deux points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def is_pinch(self, hand_data):
        """Détecte si le geste 'pinch' (pouce + index rapprochés) est actif"""
        dist = self.distance(hand_data['thumb'], hand_data['index'])
        return dist < 30