"""Draws a hand as a filled silhouette with a traced edge, which reads far better than a skeleton."""

from collections import OrderedDict

import pygame

from aslgame import theme
from aslgame.hand import FINGERS, PALM_OUTLINE, WRIST
from aslgame.matching.normalize import MIRROR_X


def stamp_hand(surface, points_xy, palm_px, color):
    """Fill the hand area: palm polygon plus a rounded capsule along each finger bone."""
    pygame.draw.polygon(surface, color, [points_xy[i] for i in PALM_OUTLINE])
    for name, joints in FINGERS.items():
        width_px = max(2, int(palm_px * (theme.THUMB_WIDTH_PALMS if name == "Thumb" else theme.FINGER_WIDTH_PALMS)))
        chain = (WRIST,) + joints if name == "Thumb" else joints
        for start, end in zip(chain, chain[1:]):
            pygame.draw.line(surface, color, points_xy[start], points_xy[end], width_px)
        for joint in chain:
            pygame.draw.circle(surface, color, points_xy[joint], width_px // 2)


def render_silhouette(normalized, palm_px, matched):
    """Return (surface, wrist position inside it) for a normalized hand at a given palm size."""
    pad_px = int(palm_px) + theme.GHOST_EDGE_DARK_PX
    points = normalized[:, :2] * palm_px
    origin = points.min(axis=0) - pad_px
    size = (points.max(axis=0) - origin + pad_px).astype(int)
    xy = [tuple(p) for p in (points - origin).tolist()]

    mask_surface = pygame.Surface(size, pygame.SRCALPHA)
    stamp_hand(mask_surface, xy, palm_px, (255, 255, 255, 255))
    edge = pygame.mask.from_surface(mask_surface).outline()

    surface = pygame.Surface(size, pygame.SRCALPHA)
    stamp_hand(surface, xy, palm_px, theme.GHOST_MATCHED_FILL if matched else theme.GHOST_FILL)
    # Faint finger lines inside show fingers folded over the palm.
    for name, joints in FINGERS.items():
        pygame.draw.lines(surface, theme.GHOST_INNER, False, [xy[j] for j in joints], theme.GHOST_INNER_PX)
    if len(edge) > 2:
        light = theme.ACCENT if matched else theme.GHOST_EDGE_LIGHT
        pygame.draw.lines(surface, theme.GHOST_EDGE_DARK, True, edge, theme.GHOST_EDGE_DARK_PX)
        pygame.draw.lines(surface, light, True, edge, theme.GHOST_EDGE_LIGHT_PX)
    return surface, (-origin).tolist()


class GhostRenderer:
    """Caches silhouettes by sign, side, size, and state, so drawing is a blit."""

    def __init__(self):
        self._cache = OrderedDict()

    def silhouette(self, sign, palm_px, is_left, matched):
        step = theme.GHOST_SIZE_STEP_PX
        palm_px = max(step, round(palm_px / step) * step)
        key = (sign.name, palm_px, is_left, matched)
        if key not in self._cache:
            shape = sign.outline * MIRROR_X if is_left else sign.outline
            self._cache[key] = render_silhouette(shape, palm_px, matched)
            if len(self._cache) > theme.GHOST_CACHE_SIZE:
                self._cache.popitem(last=False)
        self._cache.move_to_end(key)
        return self._cache[key]

    def draw(self, screen, sign, wrist_px, palm_px, is_left, matched):
        surface, wrist_offset = self.silhouette(sign, palm_px, is_left, matched)
        screen.blit(surface, (wrist_px[0] - wrist_offset[0], wrist_px[1] - wrist_offset[1]))


def draw_finger_fixes(screen, ghost_px, finger_names):
    """Trace the fingers that need fixing in a warning color on top of the ghost."""
    for name in finger_names:
        chain = FINGERS[name]
        pygame.draw.lines(screen, theme.FINGER_FIX, False, [tuple(ghost_px[j, :2].tolist()) for j in chain], theme.FINGER_FIX_PX)
        tip = tuple(ghost_px[chain[-1], :2].tolist())
        pygame.draw.circle(screen, theme.FINGER_FIX, tip, theme.FINGER_FIX_PX * 2, theme.BORDER_PX)
