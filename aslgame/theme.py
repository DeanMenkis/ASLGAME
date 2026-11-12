"""Visual values: grid, sizes, palette, fonts."""

# Grid
GRID_PX = 8
MARGIN_PX = GRID_PX * 4

# Palette: paper and three spot inks. Inks multiply where they overlap, as on a press; nothing is ever black.
PAPER = (236, 228, 212)
PAPER_SHADE = (214, 203, 182)
BLUE = (40, 58, 160)
RED = (255, 72, 80)
YELLOW = (255, 208, 30)


def over(*inks):
    """The color of inks printed over each other on white."""
    color = (255, 255, 255)
    for ink in inks:
        color = tuple(color[i] * ink[i] // 255 for i in range(3))
    return color


def tint(ink, amount):
    """An ink screened back toward paper: 1.0 is solid, 0.0 is bare paper."""
    return tuple(int(PAPER[i] + (ink[i] - PAPER[i]) * amount) for i in range(3))


PLUM = over(BLUE, RED)  # the darkest color on the sheet
ORANGE = over(RED, YELLOW)
BLUE_SOFT = tint(BLUE, 0.6)
BLUE_FAINT = tint(BLUE, 0.32)
BACKGROUND = PAPER
LIVE_HAND = (0, 200, 255)
SHADE = (*BLUE, 150)
# Every panel casts a hard shadow in blue, like a second plate printed out of register.
SHADOW_PX = 6

# Type
# System font families in order of preference; pygame falls back to its own font if none exist.
FONT_FAMILIES = "avenirnext,helveticaneue,helvetica,arial"
# Wood type: a fat slab for letters, numbers, and titles, and a condensed gothic for labels.
SLAB_FAMILIES = "rockwell,rockwellextrabold,arialblack,georgia"
LABEL_FAMILIES = "dincondensed,avenirnextcondensed,impact,arialnarrow,arial"
FONT_SIZE_LABEL_PX = 26
FONT_SIZE_SLAB_BODY_PX = 26
FONT_SIZE_SLAB_MODE_PX = 40
FONT_SIZE_SLAB_TITLE_PX = 104
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
# The band's lower edge breaks into dots, so what sits on it is centred a little above the middle.
TOP_BAR_CENTER_Y_PX = GRID_PX * 4 + 2
ICON_BUTTON_PX = GRID_PX * 7
KEY_CHIP_MIN_WIDTH_PX = GRID_PX * 10

# Ghost hand silhouette: a paper cut-out with a blue edge; it turns yellow when the hand matches.
GHOST_FILL = (*PAPER, 120)
GHOST_MATCHED_FILL = (*YELLOW, 150)
GHOST_EDGE_DARK = (*BLUE, 235)
GHOST_EDGE_LIGHT = PAPER
GHOST_EDGE_DARK_PX = 8
GHOST_EDGE_LIGHT_PX = 3
GHOST_INNER = (*BLUE, 120)
GHOST_INNER_PX = 2
FINGER_FIX = RED
FINGER_FIX_PX = 7
# Widths in palm sizes, so the silhouette scales with the hand.
FINGER_WIDTH_PALMS = 0.24
THUMB_WIDTH_PALMS = 0.28
# Silhouettes are cached per palm size rounded to this step.
GHOST_SIZE_STEP_PX = 4
GHOST_CACHE_SIZE = 48
REFERENCE_CARD_SIZE_PX = (GRID_PX * 26, GRID_PX * 32)
REFERENCE_PALM_PX = GRID_PX * 8
CARD_LETTER_PX = 60

# Finger colors option: one tint per finger, from the Okabe-Ito palette, which stays distinct with color blindness.
FINGER_TINTS = {
    "Thumb": (230, 159, 0, 150),
    "Index": (86, 180, 233, 150),
    "Middle": (0, 158, 115, 150),
    "Ring": (240, 228, 66, 150),
    "Pinky": (204, 121, 167, 150),
}

# Judgements. Each has an ink, and also text and a shape: dots under the letter (3, 2, 1), or a strike for a miss.
JUDGEMENT_COLORS = {"PERFECT": RED, "GOOD": BLUE, "OK": YELLOW, "MISS": tint(BLUE, 0.45)}
# The ink of text printed on each judgement's color.
JUDGEMENT_TEXT_COLORS = {"PERFECT": PAPER, "GOOD": PAPER, "OK": BLUE, "MISS": PAPER}
JUDGEMENT_DOTS = {"PERFECT": 3, "GOOD": 2, "OK": 1, "MISS": 0}
STRIP_DOT_RADIUS_PX = 4
STRIP_DOT_STEP_PX = GRID_PX + 4
STRIP_LABEL_LIFT_PX = GRID_PX // 2

# Recall mode
HINT_BUTTON_WIDTH_PX = GRID_PX * 14

# Motion signs (J, Z)
GUIDE = RED
TRAIL = YELLOW
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

# Heat: the ink of rings and numbers as the multiplier climbs.
HEAT_STOPS = ((0.0, BLUE), (0.4, RED), (1.0, ORANGE))
