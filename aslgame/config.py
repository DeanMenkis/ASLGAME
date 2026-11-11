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

# Levels: Easy, Medium, Hard. Each sets how many beats a sign gets and which words are drawn.
LEVEL_NAMES = ("Easy", "Medium", "Hard")
LEVEL_BEATS_PER_NOTE = (4, 2, 1)
# Words up to this many letters belong to each level; longer ones are Hard.
LEVEL_MAX_WORD_LETTERS = (4, 6)
# Run lengths offered in the menu. A song shorter than the choice plays to its end.
LENGTHS_S = (30, 60, 120, 240)
DEFAULT_LENGTH_S = 60

# Rhythm mode
RHYTHM_BPM = 90
APPROACH_BEATS = 3
RHYTHM_LEAD_IN_S = 2.5
# Two tracker results in a row: enough to drop a one-frame flicker, short enough for fast fingerspelling.
RHYTHM_HOLD_S = 0.06
# A sign made before its beat is held and lands on the beat. After the beat, lateness is judged
# as a share of the hit window: up to this share is Perfect, then Good, then OK.
HIT_WINDOW_S = 0.5
PERFECT_FRACTION = 0.3
GOOD_FRACTION = 0.6
# Fast charts shrink the window so one sign's window never runs deep into the next sign's time.
HIT_WINDOW_INTERVAL_FRACTION = 0.6
FEEDBACK_S = 0.5
# J and Z are drawn, so they get at least two note slots and at least this long.
MOTION_MIN_SLOT_S = 1.4
MOTION_MIN_SLOTS = 2

# Music mode stops this long before the song's end, so the last sign is never cut off.
MUSIC_END_MARGIN_S = 3.0
MUSIC_FADE_MS = 1200

# Rush mode: no beat. Each sign must land before its fuse burns down, and faster is better.
RUSH_FUSE_S = (6.0, 4.5, 3.0)
RUSH_PERFECT_S = 0.8
RUSH_GOOD_S = 1.6
# Drawn letters take longer, so their speed limits are stretched by this.
RUSH_MOTION_FACTOR = 2.0
# A word signed without a miss adds time to the clock.
RUSH_WORD_BONUS_S = 0.75
RUSH_LEAD_IN_S = 0.3
# The quickest anyone signs through the camera, used to draw enough words for a run.
RUSH_FASTEST_SIGN_S = 0.1

# Music: Rush on a song. Each sign's fuse is this many beats per level; Perfect and Good are shares of it.
FLOW_FUSE_BEATS = (6, 4, 3)
FLOW_PERFECT_FRACTION = 0.35
FLOW_GOOD_FRACTION = 0.65
# A sign landing this close to a beat scores this much more.
ON_BEAT_WINDOW_S = 0.09
ON_BEAT_BONUS = 1.5

# Ink and fire. The multiplier heats the screen: ink at first, then embers, flames, and ablaze; a miss puts it out.
# Low enough that a few clean signs light it: embers after about 5 in a row, flames after about 15, ablaze after about 30
# (fewer with Perfects).
FIRE_START_MULT = 1.1
FIRE_FULL_MULT = 3.0
HEAT_RISE_PER_S = 0.9
HEAT_FALL_PER_S = 0.5
HEAT_STAGES = (0.08, 0.35, 0.7)  # embers, flames, ablaze
# A long hot streak burns blue-white.
BLUE_FIRE_MULT = 5.0
# After a fire goes out the camera dims and loses some colour, then recovers over this long.
ASH_S = 1.2
# The camera keeps its own colour. Cold is a touch muted, ablaze a touch richer (negative means more saturated),
# and a fire going out drains at most this much colour for a moment.
GRADE_GRAY_COLD = 0.1
GRADE_GRAY_HOT = -0.15
GRADE_GRAY_ASH = 0.45
# Fire is drawn at a quarter size and scaled up, which blurs it into glow for free.
FIRE_LAYER_SCALE = 4
FIRE_BUOYANCY = 260.0
FIRE_MAX_PARTICLES = 700
FIRE_BOTTOM_RATE = 240.0  # flames a second along the bottom when fully ablaze
FIRE_TIP_RATE = 70.0  # flames a second at the fuse's burning tip
SPARK_RATE = 45.0
SMOKE_LIFE_S = 1.8
ASH_FLAKE_LIFE_S = 2.8
# Brush strokes
BRUSH_STEPS = 140
BRUSH_STRANDS = 6
BRUSH_DRY_FROM = 0.8
SPLAT_LIFE_S = 1.2
STAMP_LIFE_S = 0.85
SLAM_S = 0.09

# Countdown before a timed run
COUNTDOWN_STEPS = 3
COUNTDOWN_STEP_S = 0.6

# Multiplier: x1.0 plus a little per hit in the combo, more per Perfect in a row, plus speed. Capped at x10.
COMBO_CAP = 100
COMBO_BONUS = 0.05
PERFECT_STREAK_BONUS = 0.1
PERFECT_STREAK_CAP = 4.0
SPEED_BONUS = 1.0
MULTIPLIER_MAX = 10.0
WORD_BONUS_PER_SIGN = 50
WORD_BONUS_MIN_SIGNS = 2
COMBO_MILESTONES = (10, 25, 50, 100, 200)
# Arcade effects
PARTICLES_PER_HIT = 14
PARTICLES_PER_TIER = 4
PARTICLES_MAX_BURST = 60
PARTICLE_SPEED_MIN = 150.0
PARTICLE_SPEED_MAX = 420.0
PARTICLE_GRAVITY = 600.0
PARTICLE_LIFE_S = 0.7
POP_LIFE_S = 0.9
BANNER_LIFE_S = 1.1
WORD_BANNER_LIFE_S = 1.3
SHOCKWAVE_LIFE_S = 0.4
SCORE_ROLL_RATE = 0.15
PULSE_S = 0.3
SHAKE_S = 0.22
# Embers rise from the multiplier from this tier up, this many a second per tier.
EMBER_MIN_TIER = 3
EMBERS_PER_TIER_PER_S = 5.0
EMBER_LIFE_S = 0.9
# The hit sound climbs one step of its scale every this many hits in a combo.
PITCH_STEP_COMBO = 4
GRADES = (("S", 0.95), ("A", 0.88), ("B", 0.75), ("C", 0.55), ("D", 0.0))
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
