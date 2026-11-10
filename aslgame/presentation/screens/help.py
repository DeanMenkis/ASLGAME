"""Optional keys panel, opened with H or the ? button."""

from aslgame import theme
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.overlay import Overlay
from aslgame.presentation.ink import torn_slip
from aslgame.presentation.ui import draw_key_chip

SECTIONS = (
    ("Menu", (("Left  Right", "Mode"), ("Up  Down", "Choose"), ("1 2 3  Tab", "Level"), ("L", "Length"), ("Enter", "Begin"), ("Esc", "Quit"))),
    ("Playing", (("Esc  P", "Pause"), ("Tab", "Hint in Recall"))),
    ("Paused", (("Esc  Space", "Resume"), ("M", "Menu"))),
    ("Results", (("R", "Retry"), ("M", "Menu"))),
    ("Anywhere", (("C", "Finger colors"), ("S", "Sound"), ("F", "Fullscreen"), ("F3", "Performance"))),
)
LEFT_COLUMN_SECTIONS = 3
COLUMN_WIDTH_PX = theme.GRID_PX * 40
PANEL_SIZE_PX = (COLUMN_WIDTH_PX * 2 + theme.GRID_PX * 8, theme.GRID_PX * 80)


def build_panel(fonts):
    panel = torn_slip(PANEL_SIZE_PX, theme.SURFACE, seed=23)
    draw_text_centered(panel, fonts.medium.render("Keys", True, theme.INK), (PANEL_SIZE_PX[0] // 2, theme.GRID_PX * 5))
    x_px = [theme.GRID_PX * 4, theme.GRID_PX * 4 + COLUMN_WIDTH_PX + theme.GRID_PX * 2]
    y_px = [theme.GRID_PX * 10, theme.GRID_PX * 10]
    for index, (title, rows) in enumerate(SECTIONS):
        column = 0 if index < LEFT_COLUMN_SECTIONS else 1
        panel.blit(fonts.small.render(title.upper(), True, theme.SEAL), (x_px[column], y_px[column]))
        y_px[column] += theme.GRID_PX * 4
        for key, action in rows:
            center_y_px = y_px[column] + theme.GRID_PX * 2
            chip = draw_key_chip(panel, fonts.small, key, (x_px[column], center_y_px))
            label = fonts.body.render(action, True, theme.INK)
            panel.blit(label, label.get_rect(midleft=(chip.right + theme.GRID_PX * 2, center_y_px)))
            y_px[column] += theme.GRID_PX * 5
        y_px[column] += theme.GRID_PX * 2
    return panel


class HelpPanel(Overlay):
    def __init__(self, fonts, size_px):
        super().__init__(build_panel(fonts), size_px)
