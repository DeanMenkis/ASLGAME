"""Tunable values. Visual values live in theme.py."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "models" / "hand_landmarker.task"
SIGNS_DIR = ROOT_DIR / "data" / "signs"
CHARTS_DIR = ROOT_DIR / "data" / "charts"
MEDIA_DIR = ROOT_DIR / "media"
SETTINGS_PATH = ROOT_DIR / "settings.json"
RECORDS_PATH = ROOT_DIR / "records.json"
LETTERS_PATH = ROOT_DIR / "letters.json"

# Camera
CAMERA_INDEX = 0
CAMERA_WIDTH_PX = 1280
CAMERA_HEIGHT_PX = 720
CAMERA_FPS = 30
CAMERA_MIRROR = True
CAMERA_RETRY_S = 0.05
# Low light warning: shown when the picture stays darker than this, on a 0 to 255 scale.
LOW_LIGHT_LEVEL = 45
LOW_LIGHT_DELAY_S = 1.5
BRIGHTNESS_SAMPLE_STEP = 16
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
MATCH_HOLD_S = 0.4
# How far another sign may outscore the target before the target is rejected.
MATCH_RIVAL_MARGIN = 0.05
# A finger is flagged when its joints sit this far from the target, in palm sizes.
# Correct signs stay under it about 90% of the time; other letters mostly go over.
FINGER_HINT_LIMIT = 0.55

# Learn and Recall draw words from a deck until a run has about this many signs.
LEARN_RUN_SIGNS = 18

# Letter mastery, kept between runs. Each letter's score starts in the middle and moves this share of the way
# toward every new result, so two Perfects make a letter known and one miss makes it weak again.
MASTERY_START = 0.5
MASTERY_RATE = 0.3
MASTERY_KNOWN = 0.75
# The Practise deck: an untested letter needs this much practice (a weak one needs up to 1, a known one none).
# A word's weight is its letters' mean need raised to this power, which about doubles how often weak letters come up,
# and every word keeps a small weight so the deck never runs dry.
MASTERY_UNTESTED_NEED = 0.4
PRACTISE_SHARPNESS = 4
PRACTISE_BASE_WEIGHT = 0.0005

# Levels: Easy, Medium, Hard. Each sets which words are drawn and how long a sign's fuse is.
LEVEL_NAMES = ("Easy", "Medium", "Hard")
# Words up to this many letters belong to each level; longer ones are Hard.
LEVEL_MAX_WORD_LETTERS = (4, 6)
# Run lengths offered in the menu. A song shorter than the choice plays to its end.
LENGTHS_S = (30, 60, 120, 240)
DEFAULT_LENGTH_S = 60

# Charts leave at least this many beats before the first beat that counts.
CHART_LEAD_BEATS = 4
# Two tracker results in a row: enough to drop a one-frame flicker, short enough for fast fingerspelling.
TIMED_HOLD_S = 0.06

# Music mode stops this long before the song's end, so the last sign is never cut off.
MUSIC_END_MARGIN_S = 3.0
MUSIC_FADE_MS = 1200

# Music: the next sign appears the moment one lands. Each sign's fuse is this many beats per level,
# and Perfect and Good are shares of it.
FUSE_BEATS = (6, 4, 3)
PERFECT_FRACTION = 0.35
GOOD_FRACTION = 0.65
# Drawn letters (J, Z) take longer, so their fuse is stretched by this.
MOTION_FUSE_FACTOR = 2.0
# A sign landing this close to a beat scores this much more.
ON_BEAT_WINDOW_S = 0.09
ON_BEAT_BONUS = 1.5
# The quickest anyone signs through the camera, used to draw enough words for a run.
FASTEST_SIGN_S = 0.1

# The press. The multiplier is heat: the camera is printed in blue and red at first, a yellow plate joins as heat rises,
# and halftone dots climb from the bottom edge. A miss slips the plates out of register and the heat is gone.
# Low enough that a few clean signs show it: about 5 in a row to start, about 30 for full heat (fewer with Perfects).
HEAT_START_MULT = 1.1
HEAT_FULL_MULT = 3.0
HEAT_RISE_PER_S = 0.9
HEAT_FALL_PER_S = 0.5
HEAT_STAGES = (0.08, 0.35, 0.7)  # warm, hot, full colour
# From this multiplier the press runs flat out: the dots at the bottom overprint in all three inks.
FULL_PRESS_MULT = 5.0
# After a miss the plates slide back into register over this long.
SLIP_S = 1.2
# Camera print. Printed at 1/PRINT_SCALE size and scaled up. Each plate is part smooth tone and part dots.
PRINT_SCALE = 2
PRINT_PITCH_PX = 3.5
PRINT_ANGLES_DEG = (15, 75, 45)  # blue, red, yellow
PRINT_DOTS = 0.5
PRINT_DOT_CONTRAST = 2.5
PRINT_MAX_INK = 0.9
PRINT_BLUE_GAIN = 1.1
PRINT_BLUE_CURVE = 2.3
PRINT_RED_GAIN = 2.0
PRINT_RED_HEAT_GAIN = 0.6
PRINT_YELLOW_GAIN = 2.4
PRINT_YELLOW_BASE = 0.25
PRINT_SLIP_PX = 22
# Dots rising from the bottom edge: how tall the field is at full heat, and the spacing of its dots.
DOT_FIELD_HEIGHT_PX = 260
DOT_FIELD_PITCH_PX = 20
# Paper chads thrown by hits once the press is warm.
CHADS_MAX = 260
CHAD_LIFE_S = 1.1
STAMP_LIFE_S = 0.85
SLAM_S = 0.09

# Countdown before a timed run
COUNTDOWN_STEPS = 3
COUNTDOWN_STEP_S = 0.6

# Multiplier: x1.0 plus a little per hit in the combo, and more per Perfect in a row. Capped at x10.
COMBO_CAP = 100
COMBO_BONUS = 0.05
PERFECT_STREAK_BONUS = 0.1
PERFECT_STREAK_CAP = 4.0
MULTIPLIER_MAX = 10.0
WORD_BONUS_PER_SIGN = 50
WORD_BONUS_MIN_SIGNS = 2
COMBO_MILESTONES = (10, 25, 50, 100, 200)
# Arcade effects
PARTICLE_SPEED_MIN = 150.0
PARTICLE_SPEED_MAX = 420.0
PARTICLE_GRAVITY = 600.0
POP_LIFE_S = 0.9
BANNER_LIFE_S = 1.1
WORD_BANNER_LIFE_S = 1.3
SCORE_ROLL_RATE = 0.15
PULSE_S = 0.3
SHAKE_S = 0.22
# The hit sound climbs one step of its scale every this many hits in a combo.
PITCH_STEP_COMBO = 4
GRADES = (("S", 0.95), ("A", 0.88), ("B", 0.75), ("C", 0.55), ("D", 0.0))
RESULTS_WEAKEST_COUNT = 3

# Dataset import
# The dataset normalizes x and y by frame width and height; its frames are treated as 16:9.
DATASET_ASPECT = 16 / 9
DATASET_OUTLIER_FACTOR = 2.0
DATASET_MAX_SAMPLES = 80
# J borrows the I handshape, so its dataset samples are not imported.
DATASET_SKIP = ("J",)
# Z was recorded mid-stroke; only samples pointing up make a clear picture of its handshape.
DATASET_POINTING_UP = ("Z",)
POINTING_UP_PALMS = 0.6
SIDEWAYS_LETTERS = ("G", "H", "P", "Q")

# Motion signs (J, Z). A stroke passes by its shape, or by touching the guide's checkpoints in order.
MOTION_WINDOW_S = 3.5
MOTION_SHAPE_GRACE_S = 0.7
MOTION_RESAMPLE_POINTS = 24
MOTION_MIN_POINTS = 8
MOTION_START_STEP = 2
MOTION_MIN_EXTENT_PALMS = 0.7
MOTION_MATCH_DISTANCE = 0.2
# Each axis is scaled on its own, so a wide or tall drawing still fits. The short axis is never
# stretched by more than this, or a straight line would be blown up into noise.
MOTION_MAX_STRETCH = 2.5
# Fingertip positions are averaged over this many results to calm tracking jitter.
MOTION_SMOOTH_POINTS = 3
# Checkpoints: how close the fingertip must pass, in palm sizes, and how long it may stall before the guide resets.
CHECKPOINT_RADIUS_PALMS = 0.45
CHECKPOINT_STALL_S = 1.5
# The guide follows a fingertip that rests within this distance of where it was placed.
GUIDE_REST_PALMS = 0.25
GUIDE_REST_POINTS = 5
# A finger counts as straight when its tip is this much farther from the wrist than its middle joint.
# Straight fingers measure about 1.3 and folded ones 0.85 or less.
EXTENDED_RATIO = 1.1
TRAIL_POINTS = 60

# Capture tool
CAPTURE_COUNTDOWN_S = 2.0
CAPTURE_SAMPLES_PER_BURST = 15

# Debug overlay
DEBUG_OVERLAY_ON_START = False
# The tracked skeleton over the player's hand is only drawn with the debug overlay.
DEBUG_REFRESH_S = 0.25
FPS_SMOOTHING = 0.1
