"""Draws the path of a motion sign (J, Z) as a guide, and the player's own stroke as a trail."""

import pygame

from aslgame import theme
from aslgame.game.motion import oriented_path, resample


def guide_points(motion, start_px, palm_px, is_left):
    path = resample(oriented_path(motion, is_left), theme.GUIDE_POINTS)
    start_x, start_y, palm_px = float(start_px[0]), float(start_px[1]), float(palm_px)
    return [(start_x + x * palm_px, start_y + y * palm_px) for x, y in path.tolist()]


def draw_guide(screen, points, phase=None):
    """Dashed path with an arrowhead; phase, from 0 to 1, moves a dot along it to show direction and speed."""
    for index in range(0, len(points) - 1, 2):
        pygame.draw.line(screen, theme.GHOST_EDGE_DARK, points[index], points[index + 1], theme.GUIDE_LINE_PX + 4)
        pygame.draw.line(screen, theme.GUIDE, points[index], points[index + 1], theme.GUIDE_LINE_PX)
    draw_arrowhead(screen, points[-2], points[-1])
    pygame.draw.circle(screen, theme.GUIDE, points[0], theme.GUIDE_DOT_PX, theme.BORDER_PX)
    if phase is not None:
        dot = points[min(len(points) - 1, int(phase * len(points)))]
        pygame.draw.circle(screen, theme.GHOST_EDGE_DARK, dot, theme.GUIDE_DOT_PX + 2)
        pygame.draw.circle(screen, theme.GUIDE, dot, theme.GUIDE_DOT_PX)


def draw_arrowhead(screen, before, tip):
    direction = pygame.Vector2(tip) - pygame.Vector2(before)
    if direction.length() == 0:
        return
    direction.scale_to_length(theme.GUIDE_ARROW_PX)
    left = pygame.Vector2(tip) - direction.rotate(30)
    right = pygame.Vector2(tip) - direction.rotate(-30)
    pygame.draw.polygon(screen, theme.GUIDE, [tip, left, right])


def draw_trail(screen, points_px):
    """The player's stroke so far, so they can see what they drew."""
    if len(points_px) > 1:
        pygame.draw.lines(screen, theme.TRAIL, False, points_px, theme.TRAIL_LINE_PX)
