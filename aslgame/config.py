"""Tunable values. Visual values live in theme.py."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "models" / "hand_landmarker.task"
SIGNS_DIR = ROOT_DIR / "data" / "signs"

# Camera
CAMERA_INDEX = 0
CAMERA_WIDTH_PX = 1280
CAMERA_HEIGHT_PX = 720
CAMERA_FPS = 30
CAMERA_MIRROR = True
CAMERA_RETRY_S = 0.05
CAMERA_OPEN_TIMEOUT_S = 30.0
CAMERA_OPEN_RETRY_S = 1.0

# Main loop
TARGET_FPS = 60
WINDOW_TITLE = "ASLGAME"

# Tracking
MAX_HANDS = 1
MIN_HAND_DETECTION_CONFIDENCE = 0.5
MIN_HAND_PRESENCE_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
TRACKER_WAIT_TIMEOUT_S = 0.1
THREAD_JOIN_TIMEOUT_S = 1.0

# Matching
# Mean normalized joint distance at which the score falls to zero.
MATCH_ZERO_SCORE_DISTANCE = 0.6
MATCH_THRESHOLD = 0.75
# Lower than MATCH_THRESHOLD so a hold survives small dips in score.
MATCH_RELEASE_THRESHOLD = 0.65
MATCH_HOLD_S = 0.6
# How far another sign may outscore the target before the target is rejected.
MATCH_RIVAL_MARGIN = 0.05

# Learn mode. J and Z need motion, which handshape templates cannot capture.
LEARN_WORDS = ("HI", "ASL", "CAB", "LOVE", "GOOD DAY", "THANK YOU")

# Dataset import
# The dataset normalizes x and y by frame width and height; its frames are treated as 16:9.
DATASET_ASPECT = 16 / 9
DATASET_OUTLIER_FACTOR = 2.0
DATASET_MAX_SAMPLES = 80
MOTION_LETTERS = ("J", "Z")
SIDEWAYS_LETTERS = ("G", "H", "P", "Q")

# Capture tool
CAPTURE_COUNTDOWN_S = 2.0
CAPTURE_SAMPLES_PER_BURST = 15

# Debug overlay
DEBUG_OVERLAY_ON_START = True
DEBUG_REFRESH_S = 0.25
FPS_SMOOTHING = 0.1
