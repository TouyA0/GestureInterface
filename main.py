import sys
import time
import cv2
import numpy as np
import pyautogui
import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
from enum import Enum, auto
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import QTimer, Qt

from config import *
from core.camera_handler import CameraHandler
from core.gesture_detector import GestureDetector
from core.window_controller import WindowController

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

PINCH_ENTER  = 0.30  # distance normalisée (/ taille main) pour entrer en pinch
PINCH_EXIT   = 0.50  # distance normalisée pour sortir du pinch
PINCH_SMOOTH = 0.4   # lissage de la distance de pinch
DRAG_DELAY   = 0.50  # secondes avant que pinch → drag
CURSOR_ALPHA = 0.35  # lissage curseur
DOUBLE_CLICK_MAX  = 0.55  # fenêtre entre deux clicks pour déclencher double-click

SW_MAXIMIZE = 3
SW_RESTORE  = 9


class State(Enum):
    IDLE    = auto()
    PENDING = auto()  # pinch détecté, on attend pour savoir si click ou drag
    DRAGGING = auto()


class GestureApp(QWidget):
    def __init__(self):
        super().__init__()
        self._cursor       = None
        self._state        = State.IDLE
        self._pinch_t      = 0.0
        self._is_pinch     = False
        self._drag_hwnd    = None
        self._drag_win_pos = None
        self._drag_orig    = None
        self._last_click   = 0.0
        self._pdist_smooth = 1.0  # distance pinch lissée (normalisée)

        self.camera      = CameraHandler()
        self.detector    = GestureDetector()
        self.win_ctrl    = WindowController()
        self.camera.start()

        self.setWindowTitle("GestureInterface")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.showFullScreen()

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / REFRESH_RATE))

    # ------------------------------------------------------------------ helpers

    def _get_top_hwnd(self, x, y):
        hwnd = user32.WindowFromPoint(ctypes.wintypes.POINT(x, y))
        while True:
            parent = user32.GetParent(hwnd)
            if not parent:
                break
            hwnd = parent
        return hwnd if user32.IsWindow(hwnd) else None

    def _crop_black_bars(self, frame, thr=10):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cols = np.where(gray.max(axis=0) > thr)[0]
        rows = np.where(gray.max(axis=1) > thr)[0]
        if not len(cols) or not len(rows):
            return frame
        return frame[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]

    def _smooth(self, sx, sy):
        if self._cursor is None:
            self._cursor = (sx, sy)
        else:
            cx, cy = self._cursor
            self._cursor = (
                int(cx + (sx - cx) * CURSOR_ALPHA),
                int(cy + (sy - cy) * CURSOR_ALPHA),
            )

    # ------------------------------------------------------------------ tick

    def _tick(self):
        frame = self.camera.get_frame()
        if frame is None:
            return

        frame = self._crop_black_bars(frame)
        fh, fw = frame.shape[:2]

        results = self.detector.detect(frame)
        hands   = self.detector.get_hand_positions(results, fw, fh)

        if not hands:
            self._state    = State.IDLE
            self._is_pinch = False
            self._cursor   = None
            self.update()
            return

        hand = hands[0]
        pts  = hand['all_points']
        ix, iy = hand['index']
        tx, ty = hand['thumb']

        # Curseur lissé
        self._smooth(int(ix * self.width()), int(iy * self.height()))
        cx, cy = self._cursor

        # Taille de la main : wrist(0) → middle MCP(9) pour normaliser
        wx, wy = pts[0]
        mx, my = pts[9]
        hand_size = max(np.hypot((wx - mx) * fw, (wy - my) * fh), 1)

        # Distance pinch normalisée + lissée (stable quelle que soit la distance caméra)
        raw_norm = np.hypot((ix - tx) * fw, (iy - ty) * fh) / hand_size
        self._pdist_smooth += (raw_norm - self._pdist_smooth) * PINCH_SMOOTH

        # Hysteresis sur distance normalisée
        if self._is_pinch:
            pinch = self._pdist_smooth < PINCH_EXIT
        else:
            pinch = self._pdist_smooth < PINCH_ENTER

        now = time.monotonic()

        # ---- Machine d'état ----
        if self._state == State.IDLE:
            if pinch and not self._is_pinch:
                self._state  = State.PENDING
                self._pinch_t = now

        elif self._state == State.PENDING:
            if not pinch:
                if now - self._last_click < DOUBLE_CLICK_MAX:
                    # Double-click → toggle maximise
                    hwnd = self._get_top_hwnd(cx, cy)
                    if hwnd:
                        if user32.IsZoomed(hwnd):
                            user32.ShowWindow(hwnd, SW_RESTORE)
                        else:
                            user32.ShowWindow(hwnd, SW_MAXIMIZE)
                    self._last_click = 0.0  # reset pour éviter triple-click
                else:
                    # Simple click
                    pyautogui.click(cx, cy)
                    self._last_click = now
                self._state = State.IDLE
            elif now - self._pinch_t >= DRAG_DELAY:
                # Maintenu assez longtemps → DRAG
                hwnd = self._get_top_hwnd(cx, cy)
                if hwnd:
                    r = RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(r))
                    self._drag_hwnd = hwnd
                    self._drag_win_pos = (r.left, r.top)
                    self._drag_orig = (cx, cy)
                    self._state = State.DRAGGING

        elif self._state == State.DRAGGING:
            if not pinch:
                self._drag_hwnd = None
                self._state = State.IDLE
            elif self._drag_hwnd:
                dx = cx - self._drag_orig[0]
                dy = cy - self._drag_orig[1]
                wx, wy = self._drag_win_pos
                r = RECT()
                user32.GetWindowRect(self._drag_hwnd, ctypes.byref(r))
                user32.SetWindowPos(self._drag_hwnd, 0,
                                    wx + dx, wy + dy,
                                    r.right - r.left, r.bottom - r.top, 0)

        self._is_pinch = pinch
        self.update()

    # ------------------------------------------------------------------ render

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        if self._cursor is None:
            return

        x, y = self._cursor
        painter.setPen(Qt.PenStyle.NoPen)

        if self._state == State.DRAGGING:
            # Rouge — drag actif
            painter.setBrush(QBrush(QColor(255, 70, 70, 230)))
            painter.drawEllipse(x - 20, y - 20, 40, 40)

        elif self._state == State.PENDING:
            # Orange + arc de progression vers drag
            progress = min((time.monotonic() - self._pinch_t) / DRAG_DELAY, 1.0)
            painter.setBrush(QBrush(QColor(255, 165, 0, 200)))
            painter.drawEllipse(x - 12, y - 12, 24, 24)
            from PyQt6.QtGui import QPen as _QPen
            from PyQt6.QtCore import QRectF
            pen = _QPen(QColor(255, 255, 255, 200), 3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(QRectF(x - 18, y - 18, 36, 36),
                            90 * 16, int(-360 * 16 * progress))

        else:
            # Blanc — curseur normal
            painter.setBrush(QBrush(QColor(255, 255, 255, 210)))
            painter.drawEllipse(x - 10, y - 10, 20, 20)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor(255, 255, 255, 70))
            painter.drawEllipse(x - 22, y - 22, 44, 44)

    # ------------------------------------------------------------------ events

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
