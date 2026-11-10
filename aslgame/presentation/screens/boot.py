"""Shown until the tracker has produced its first result."""

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.presentation.draw import draw_ring


class BootScreen:
    def handle_event(self, event):
        return None

    def update(self, now_s, result):
        return Action.READY if result is not None else None

    def draw(self, screen, now_s, hand):
        center_px = (screen.get_width() // 2, screen.get_height() // 2)
        draw_ring(screen, center_px, theme.RING_RADIUS_PX, now_s % 1.0, theme.PAPER)
