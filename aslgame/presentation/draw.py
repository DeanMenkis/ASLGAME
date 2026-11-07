"""Drawing primitives shared by every screen."""

import math

import pygame

from aslgame import theme
from aslgame.hand import BONES

# pygame angles run counterclockwise from the right, so the top is a quarter turn.
TOP_ANGLE = math.pi / 2
FULL_TURN = 2 * math.pi


def draw_camera(screen, frame):
    height_px, width_px = frame.rgb.shape[:2]
    # frombuffer wraps the array without copying it.
    image = pygame.image.frombuffer(frame.rgb.data, (width_px, height_px), "RGB")
    screen.blit(image, (0, 0))


def draw_hand(screen, points_px, color, line_px, joint_radius_px, filled):
    xy = points_px[:, :2].tolist()
    for start, end in BONES:
        pygame.draw.line(screen, color, xy[start], xy[end], line_px)
    joint_width_px = 0 if filled else line_px
    for point in xy:
        pygame.draw.circle(screen, color, point, joint_radius_px, joint_width_px)


def draw_ring(screen, center_px, radius_px, fraction, color):
    """An arc clockwise from the top. fraction 1.0 is a full ring."""
    if fraction <= 0:
        return
    rect = pygame.Rect(0, 0, radius_px * 2, radius_px * 2)
    rect.center = center_px
    if fraction >= 1:
        pygame.draw.circle(screen, color, center_px, radius_px, theme.RING_LINE_PX)
        return
    pygame.draw.arc(screen, color, rect, TOP_ANGLE - FULL_TURN * fraction, TOP_ANGLE, theme.RING_LINE_PX)


def draw_text_centered(screen, surface, center_px):
    screen.blit(surface, surface.get_rect(center=center_px))
