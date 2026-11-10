"""Drawing primitives shared by every screen."""

import math

import pygame

from aslgame import theme
from aslgame.hand import BONES

# pygame angles run counterclockwise from the right, so the top is a quarter turn.
TOP_ANGLE = math.pi / 2
FULL_TURN = 2 * math.pi
ARC_STEPS = 96


def draw_camera(screen, frame):
    pixels = frame.display if frame.display is not None else frame.rgb
    height_px, width_px = pixels.shape[:2]
    # frombuffer wraps the array without copying it.
    image = pygame.image.frombuffer(pixels.data, (width_px, height_px), "RGB")
    screen.blit(image, (0, 0))


def draw_hand(screen, points_px, color, line_px, joint_radius_px, filled):
    xy = points_px[:, :2].tolist()
    for start, end in BONES:
        pygame.draw.line(screen, color, xy[start], xy[end], line_px)
    joint_width_px = 0 if filled else theme.JOINT_OUTLINE_PX
    for point in xy:
        pygame.draw.circle(screen, color, point, joint_radius_px, joint_width_px)


def draw_ring(screen, center_px, radius_px, fraction, color):
    """An arc clockwise from the top. fraction 1.0 is a full ring."""
    if fraction <= 0:
        return
    if fraction >= 1:
        pygame.draw.circle(screen, color, center_px, radius_px, theme.RING_LINE_PX)
        return
    # A polyline with round caps: pygame's thick arcs leave pixel gaps.
    steps = max(2, int(ARC_STEPS * fraction))
    points = [(center_px[0] + math.cos(TOP_ANGLE - FULL_TURN * fraction * i / steps) * radius_px,
               center_px[1] - math.sin(TOP_ANGLE - FULL_TURN * fraction * i / steps) * radius_px) for i in range(steps + 1)]
    pygame.draw.lines(screen, color, False, points, theme.RING_LINE_PX)
    for point in (points[0], points[-1]):
        pygame.draw.circle(screen, color, point, theme.RING_LINE_PX // 2)


def draw_text_centered(screen, surface, center_px):
    screen.blit(surface, surface.get_rect(center=center_px))
