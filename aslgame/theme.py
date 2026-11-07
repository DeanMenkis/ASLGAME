"""Visual values: grid, sizes, palette, fonts."""

# Grid
GRID_PX = 8
MARGIN_PX = GRID_PX * 4

# Palette
BACKGROUND = (12, 12, 14)
INK = (240, 240, 240)
INK_DIM = (150, 150, 155)
ACCENT = (255, 196, 0)
GHOST = (255, 255, 255)
LIVE_HAND = (0, 200, 255)
PANEL = (0, 0, 0, 160)
SHADE = (0, 0, 0, 170)
SURFACE = (22, 24, 30, 225)
SURFACE_RAISED = (44, 48, 58)
SURFACE_HOVER = (58, 63, 76)
BORDER = (78, 83, 96)
ACCENT_INK = (18, 18, 20)
DISABLED = (90, 92, 100)

# Type
# System font families in order of preference; pygame falls back to its own font if none exist.
FONT_FAMILIES = "avenirnext,helveticaneue,helvetica,arial"
FONT_SIZE_SMALL_PX = 18
FONT_SIZE_BODY_PX = 24
FONT_SIZE_MEDIUM_PX = 34
FONT_SIZE_LARGE_PX = 56
FONT_SIZE_DISPLAY_PX = 140

# Hand drawing
GHOST_LINE_PX = 4
GHOST_JOINT_RADIUS_PX = 8
JOINT_OUTLINE_PX = 2
LIVE_LINE_PX = 2
LIVE_JOINT_RADIUS_PX = 3

# Score ring and countdown ring
RING_RADIUS_PX = GRID_PX * 5
RING_LINE_PX = GRID_PX

# Ghost shown before a hand appears, relative to the screen center
IDLE_GHOST_OFFSET_PX = (0, GRID_PX * 16)
IDLE_GHOST_PALM_PX = GRID_PX * 12

# Karaoke strip
STRIP_CELL_PX = GRID_PX * 8
STRIP_GAP_PX = GRID_PX
STRIP_SPACE_PX = GRID_PX * 4
STRIP_LINE_PX = 2
STRIP_CURRENT_LINE_PX = 4

# Menu
MENU_ROW_PX = GRID_PX * 9
MENU_MARKER_PX = GRID_PX

# Rhythm
HIT_RING_PALM_SCALE = 1.8
APPROACH_RING_START_SCALE = 3.0
HIT_RING_LINE_PX = 3
APPROACH_RING_LINE_PX = 6
BEAT_DOT_RADIUS_PX = GRID_PX
BEAT_PULSE_PX = GRID_PX * 2
JUDGEMENT_RISE_PX = GRID_PX * 4
HIT_FLASH_GROWTH = 0.2

# Controls
CORNER_PX = GRID_PX * 2
BUTTON_HEIGHT_PX = GRID_PX * 7
BUTTON_PADDING_PX = GRID_PX * 3
BORDER_PX = 2
ROW_HEIGHT_PX = GRID_PX * 7
CARD_WIDTH_PX = GRID_PX * 70
TOP_BAR_HEIGHT_PX = GRID_PX * 12
ICON_BUTTON_PX = GRID_PX * 7
KEY_CHIP_MIN_WIDTH_PX = GRID_PX * 10

# Ghost hand silhouette
GHOST_FILL = (255, 255, 255, 100)
GHOST_MATCHED_FILL = (255, 196, 0, 110)
GHOST_EDGE_DARK = (10, 10, 12, 220)
GHOST_EDGE_LIGHT = (255, 255, 255)
GHOST_EDGE_DARK_PX = 8
GHOST_EDGE_LIGHT_PX = 3
GHOST_INNER = (10, 10, 12, 110)
GHOST_INNER_PX = 2
FINGER_FIX = (255, 105, 90)
FINGER_FIX_PX = 7
# Widths in palm sizes, so the silhouette scales with the hand.
FINGER_WIDTH_PALMS = 0.24
THUMB_WIDTH_PALMS = 0.28
# Silhouettes are cached per palm size rounded to this step.
GHOST_SIZE_STEP_PX = 4
GHOST_CACHE_SIZE = 48
REFERENCE_CARD_SIZE_PX = (GRID_PX * 26, GRID_PX * 32)
REFERENCE_PALM_PX = GRID_PX * 8

# Finger colors option: one tint per finger, from the Okabe-Ito palette, which stays distinct with color blindness.
FINGER_TINTS = {
    "Thumb": (230, 159, 0, 150),
    "Index": (86, 180, 233, 150),
    "Middle": (0, 158, 115, 150),
    "Ring": (240, 228, 66, 150),
    "Pinky": (204, 121, 167, 150),
}

RECORD = (230, 40, 40)

# Judgements. Each also has a shape: dots under the letter (3, 2, 1), or a strike for a miss.
JUDGEMENT_COLORS = {
    "PERFECT": (70, 205, 115),
    "GOOD": (245, 210, 60),
    "OK": (245, 145, 50),
    "MISS": (235, 75, 65),
}
JUDGEMENT_DOTS = {"PERFECT": 3, "GOOD": 2, "OK": 1, "MISS": 0}
STRIP_DOT_RADIUS_PX = 4
STRIP_DOT_STEP_PX = GRID_PX + 4
STRIP_LABEL_LIFT_PX = GRID_PX // 2

# Recall mode
HINT_BUTTON_WIDTH_PX = GRID_PX * 14

# Motion signs (J, Z)
GUIDE = (120, 220, 255)
TRAIL = (255, 196, 0)
GUIDE_POINTS = 32
GUIDE_LINE_PX = 4
GUIDE_DOT_PX = 7
GUIDE_ARROW_PX = 16
TRAIL_LINE_PX = 5
GUIDE_PERIOD_S = 1.4
# The path on the reference card is drawn smaller than on the hand so it fits.
CARD_PATH_SCALE = 0.8

# Arcade effects
PARTICLE_RADIUS_PX = 6
POP_RISE_PX = GRID_PX * 10
PULSE_GROWTH = 0.35
