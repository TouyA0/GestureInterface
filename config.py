import os
from dotenv import load_dotenv

load_dotenv()

# ===== CAMÉRA =====
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
CAMERA_BRIGHTNESS = 0.7

# ===== MEDIAIPE =====
HAND_DETECTION_CONFIDENCE = 0.7
HAND_TRACKING_CONFIDENCE = 0.5
MAX_HANDS = 2

# ===== GESTES =====
GESTURE_SMOOTHING = 0.7
PINCH_THRESHOLD = 0.08
SWIPE_MIN_DISTANCE = 100
SWIPE_MIN_VELOCITY = 300

# ===== INTERFACE =====
WINDOW_OPACITY = 0.85
HUD_WIDTH = 800
HUD_HEIGHT = 460
HUD_FONT_SIZE = 12
REFRESH_RATE = 30

# ===== LOGGING =====
LOG_LEVEL = "INFO"
LOG_FILE = "gesture_interface.log"

# ===== CHEMINS =====
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")