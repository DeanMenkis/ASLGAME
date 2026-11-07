"""Tunable values. Visual values live in theme.py."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "models" / "hand_landmarker.task"
SIGNS_DIR = ROOT_DIR / "data" / "signs"
CHARTS_DIR = ROOT_DIR / "data" / "charts"
MEDIA_DIR = ROOT_DIR / "media"
SETTINGS_PATH = ROOT_DIR / "settings.json"
RECORDINGS_DIR = ROOT_DIR / "recordings"

# Camera
CAMERA_INDEX = 0
CAMERA_WIDTH_PX = 1280
CAMERA_HEIGHT_PX = 720
CAMERA_FPS = 30
CAMERA_MIRROR = True
CAMERA_RETRY_S = 0.05
CAMERA_OPEN_TIMEOUT_S = 30.0
CAMERA_OPEN_RETRY_S = 1.0

# Audio. A small buffer keeps the delay between play and sound short.
AUDIO_RATE_HZ = 44100
AUDIO_BUFFER_SAMPLES = 512
AUDIO_SAMPLE_BITS = -16  # signed 16-bit
AUDIO_CHANNELS = 2
# Mixer voices, so effects can overlap the music and each other.
AUDIO_CHANNEL_COUNT = 16
SFX_VOLUME = 0.5

# Main loop
TARGET_FPS = 60
WINDOW_TITLE = "ASLGAME"
# The window opens at this share of the screen and can be resized or made fullscreen with F.
WINDOW_SCREEN_FRACTION = 0.92

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
# A finger is flagged when its joints sit this far from the target, in palm sizes.
# Correct signs stay under it about 90% of the time; other letters mostly go over.
FINGER_HINT_LIMIT = 0.55

# Learn mode. J and Z need motion, which handshape templates cannot capture.
LEARN_WORDS = (
    "HI", "HELLO", "ASL", "CAB", "LOVE", "PLEASE", "SORRY", "THANK YOU", "WELCOME", "GOOD DAY",
    "GOOD LUCK", "GOOD MORNING", "GOOD NIGHT", "HAVE FUN", "LETS GO", "WHATS UP", "HOW ARE YOU",
    "I LOVE YOU", "BEST FRIEND", "SEE YOU LATER", "NICE TO MEET YOU", "MY NAME IS", "HAPPY BIRTHDAY",
)
ALPHABET_LABEL = "A to Y"

# Rhythm mode
RHYTHM_BPM = 90
BEATS_PER_NOTE = 4
APPROACH_BEATS = 3
RHYTHM_LEAD_IN_S = 3.0
# Short words repeat until a rhythm run has at least this many signs.
RHYTHM_MIN_SIGNS = 12
# A short hold still filters single-frame flickers without slowing play down.
RHYTHM_HOLD_S = 0.15
PERFECT_WINDOW_S = 0.15
GOOD_WINDOW_S = 0.3
HIT_WINDOW_S = 0.5
FEEDBACK_S = 0.5
COMBO_CAP = 50
COMBO_STEP = 25
SPEED_WINDOW_NOTES = 4
SPEED_UP_ACCURACY = 0.8
SPEED_DOWN_ACCURACY = 0.4
SPEED_STEP = 1.1
SPEED_MIN = 0.75
SPEED_MAX = 2.0
RESULTS_WEAKEST_COUNT = 3

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

# Demo recorder
RECORD_FPS = 30
# About two seconds of frames; beyond that frames are dropped rather than slowing the game.
RECORD_QUEUE_FRAMES = 60

# Debug overlay
DEBUG_OVERLAY_ON_START = False
# The tracked skeleton over the player's hand is only drawn with the debug overlay.
DEBUG_REFRESH_S = 0.25
FPS_SMOOTHING = 0.1
