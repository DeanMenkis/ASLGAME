"""Credits and limitations, opened from the menu."""

from aslgame import theme
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.overlay import Overlay
from aslgame.presentation.ui import make_panel

CREDITS = (
    "Letter shapes: ASL-Now fingerspelling dataset, MIT",
    "Hand tracking: MediaPipe Hand Landmarker, Apache 2.0",
    "pygame (LGPL), NumPy (BSD), OpenCV (Apache 2.0)",
    "Songs by Of Far Different Nature, CC0 and CC-BY 4.0",
    "Warm-up 90 and Hardstyle 150: made for this game",
    "Code written with Claude Code (Anthropic)",
)
LIMITS = (
    "A learning aid, not a translator",
    "Fingerspelled letters only, not word signs",
    "J and Z: the shape and path, not every detail",
    "No palm orientation, location, or face checks",
    "Letter shapes not yet checked by a fluent signer",
    "One hand at a time, in good light",
)
PANEL_SIZE_PX = (theme.GRID_PX * 90, theme.GRID_PX * 80)
LINE_STEP_PX = theme.GRID_PX * 4


def build_panel(fonts):
    panel = make_panel(PANEL_SIZE_PX, theme.SURFACE)
    draw_text_centered(panel, fonts.medium.render("About", True, theme.INK), (PANEL_SIZE_PX[0] // 2, theme.GRID_PX * 5))
    x_px = theme.GRID_PX * 5
    y_px = theme.GRID_PX * 10
    for title, lines in (("Credits", CREDITS), ("Limits", LIMITS)):
        panel.blit(fonts.small.render(title.upper(), True, theme.ACCENT), (x_px, y_px))
        y_px += LINE_STEP_PX + theme.GRID_PX
        for line in lines:
            panel.blit(fonts.body.render(line, True, theme.INK), (x_px, y_px))
            y_px += LINE_STEP_PX
        y_px += theme.GRID_PX * 3
    return panel


class AboutPanel(Overlay):
    def __init__(self, fonts, size_px):
        super().__init__(build_panel(fonts), size_px)
