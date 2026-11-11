"""The print shop: everything on screen is paper and three spot inks, printed slightly out of register.

Panels are paper stickers with a hard blue shadow. Big type is printed twice, red under blue, so the plates show.
Rings are flat ink with the picture knocked out under them, and halftone dots stand in for every soft edge.
"""

import math

import numpy as np
import pygame

from aslgame import theme
from aslgame.hand import FINGERS, PALM_OUTLINE

WHITE = (255, 255, 255)
CLEAR = (0, 0, 0, 0)
TOP = -math.pi / 2
ARC_STEPS = 120
HALO_STEPS = 12


def lerp_color(a, b, t):
    t = min(1.0, max(0.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def heat_color(heat):
    """Ink for a heat from 0 to 1: blue, then red, then red over yellow."""
    stops = theme.HEAT_STOPS
    for (h0, c0), (h1, c1) in zip(stops, stops[1:]):
        if heat <= h1:
            return lerp_color(c0, c1, (heat - h0) / (h1 - h0))
    return stops[-1][1]


# Paper


def sticker(size_px, color=theme.PAPER, edge=theme.BLUE, shadow=theme.BLUE, edge_px=3):
    """A paper panel with an ink edge and a hard shadow down and to the right. The surface is SHADOW_PX larger than size_px."""
    width, height = size_px
    drop = theme.SHADOW_PX
    surface = pygame.Surface((width + drop, height + drop), pygame.SRCALPHA)
    radius = theme.GRID_PX // 2
    if shadow is not None:
        pygame.draw.rect(surface, shadow, (drop, drop, width, height), border_radius=radius)
    pygame.draw.rect(surface, color, (0, 0, width, height), border_radius=radius)
    if edge is not None and edge_px:
        pygame.draw.rect(surface, edge, (0, 0, width, height), edge_px, border_radius=radius)
    return surface


def band(size_px, color=theme.PAPER, pitch_px=10, rows=3):
    """A paper band whose lower edge breaks up into halftone dots instead of ending in a line."""
    width, height = size_px
    surface = pygame.Surface(size_px, pygame.SRCALPHA)
    solid_px = height - pitch_px * rows
    surface.fill(color, (0, 0, width, solid_px))
    for row in range(rows):
        radius = pitch_px * 0.62 * (1 - row / rows)
        y_px = solid_px + row * pitch_px
        shift = pitch_px / 2 if row % 2 else 0
        for x_px in np.arange(-pitch_px + shift, width + pitch_px, pitch_px).tolist():
            pygame.draw.circle(surface, color, (x_px, y_px), radius)
    return surface


def dot_field(size_px, pitch_px, ink, strength=1.0):
    """A halftone gradient on white, dense at the bottom and gone at the top. Blit it with BLEND_RGB_MULT to print it."""
    width, height = size_px
    surface = pygame.Surface(size_px)
    surface.fill(WHITE)
    rows = int(height / (pitch_px * 0.5)) + 2
    for row in range(rows):
        y_px = height - row * pitch_px * 0.5
        radius = pitch_px * 0.72 * strength * (1 - row / rows) ** 1.3
        if radius < 0.6:
            continue
        shift = pitch_px / 2 if row % 2 else 0
        for x_px in np.arange(shift - pitch_px, width + pitch_px, pitch_px).tolist():
            pygame.draw.circle(surface, ink, (x_px, y_px), radius)
    return surface


def disc(radius_px, ink):
    """A flat disc of ink on white, for printing with BLEND_RGB_MULT."""
    surface = pygame.Surface((radius_px * 2, radius_px * 2))
    surface.fill(WHITE)
    pygame.draw.circle(surface, ink, (radius_px, radius_px), radius_px)
    return surface


# Type


def halo_text(font, text, color, halo=theme.PAPER, halo_px=3):
    """Text with the picture knocked out to paper around it, so ink reads over any camera print."""
    label = font.render(text, True, color)
    return knock_out(label, halo, halo_px)


def knock_out(label, halo=theme.PAPER, halo_px=3):
    """Put a paper edge around a rendered shape."""
    edge = label.copy()
    edge.fill((*halo, 255), special_flags=pygame.BLEND_RGBA_MIN)
    edge.fill((*halo, 0), special_flags=pygame.BLEND_RGBA_MAX)
    surface = pygame.Surface((label.get_width() + halo_px * 2, label.get_height() + halo_px * 2), pygame.SRCALPHA)
    for step in range(HALO_STEPS):
        angle = step / HALO_STEPS * 2 * math.pi
        surface.blit(edge, (halo_px + math.cos(angle) * halo_px, halo_px + math.sin(angle) * halo_px))
    surface.blit(label, (halo_px, halo_px))
    return surface


def overprint_text(font, text, front=theme.BLUE, back=theme.RED, shift_px=(5, 5), halo_px=0):
    """Type printed twice, out of register: the back plate shows at one side, and where the two inks meet they multiply."""
    top = font.render(text, True, front)
    under = font.render(text, True, back)
    dx, dy = shift_px
    width, height = top.get_width() + abs(dx), top.get_height() + abs(dy)
    top_at = (max(0, -dx), max(0, -dy))
    under_at = (max(0, dx), max(0, dy))
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.blit(under, under_at)
    surface.blit(top, top_at)
    top_mask, under_mask = pygame.mask.from_surface(top, 128), pygame.mask.from_surface(under, 128)
    both = top_mask.overlap_mask(under_mask, (under_at[0] - top_at[0], under_at[1] - top_at[1]))
    surface.blit(both.to_surface(setcolor=(*theme.over(front, back), 255), unsetcolor=CLEAR), top_at)
    return knock_out(surface, theme.PAPER, halo_px) if halo_px else surface


def underline(surface, left_px, y_px, width_px, color=theme.RED, height_px=6):
    """A printed rule under a choice."""
    pygame.draw.rect(surface, color, (left_px, y_px, width_px, height_px))


def make_stamp(text, font, color, text_color, angle):
    """A judgement as a block of ink with its hard shadow, set at an angle like a label slapped on."""
    label = font.render(text, True, text_color)
    block = sticker((label.get_width() + 28, label.get_height() + 10), color, edge=None, shadow=theme.PLUM)
    block.blit(label, (14, 5))
    return pygame.transform.rotozoom(block, angle, 1.0)


# Marks


def arc_points(center, radius, half_width, start_fraction, end_fraction):
    """The outline of a flat arc, clockwise from the top."""
    steps = max(4, int(ARC_STEPS * (end_fraction - start_fraction)))
    angles = TOP + 2 * np.pi * np.linspace(start_fraction, end_fraction, steps)
    cos, sin = np.cos(angles), np.sin(angles)
    outer = np.stack([center[0] + cos * (radius + half_width), center[1] + sin * (radius + half_width)], axis=1)
    inner = np.stack([center[0] + cos * (radius - half_width), center[1] + sin * (radius - half_width)], axis=1)
    return np.vstack([outer, inner[::-1]]).tolist()


def ring_point(center, radius, fraction):
    angle = TOP + 2 * math.pi * fraction
    return (center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius)


def draw_arc(surface, center, radius, fraction, width, color, knockout_px=4):
    """A flat ink arc clockwise from the top, with round ends and the picture knocked out to paper around it."""
    if fraction <= 0.005:
        return
    fraction = min(1.0, fraction)
    layers = ((theme.PAPER, width / 2 + knockout_px), (color, width / 2)) if knockout_px else ((color, width / 2),)
    for layer_color, half in layers:
        pygame.draw.polygon(surface, layer_color, arc_points(center, radius, half, 0.0, fraction))
        for end in (0.0, fraction):
            pygame.draw.circle(surface, layer_color, ring_point(center, radius, end), half)


def draw_dot_ring(surface, center, radius, from_fraction, color, dot_px=3, count=48):
    """A ring of small dots from from_fraction round to the top: the part of a fuse already spent."""
    first = int(math.ceil(from_fraction * count))
    for index in range(first, count):
        pygame.draw.circle(surface, color, ring_point(center, radius, index / count), dot_px)


def draw_registration(surface, center, radius_px, color, line_px=3, reach=1.3):
    """A printer's registration mark: a circle with cross hairs running out past it."""
    cx, cy = center
    pygame.draw.circle(surface, color, center, radius_px, line_px)
    out = radius_px * reach
    pygame.draw.line(surface, color, (cx - out, cy), (cx + out, cy), line_px)
    pygame.draw.line(surface, color, (cx, cy - out), (cx, cy + out), line_px)


def draw_crop_marks(surface, rect, color, length_px=14, gap_px=6, line_px=2):
    """Trim marks at the corners of a printed picture."""
    for x_px, x_dir in ((rect.left, -1), (rect.right, 1)):
        for y_px, y_dir in ((rect.top, -1), (rect.bottom, 1)):
            pygame.draw.line(surface, color, (x_px + x_dir * gap_px, y_px), (x_px + x_dir * (gap_px + length_px), y_px), line_px)
            pygame.draw.line(surface, color, (x_px, y_px + y_dir * gap_px), (x_px, y_px + y_dir * (gap_px + length_px)), line_px)


def starburst(radius_px, points, color, inner=0.8, edge=None):
    """A sale-sticker star: the loudest shape a poster has."""
    dim = int(radius_px * 2 + 4)
    center = dim / 2
    surface = pygame.Surface((dim, dim), pygame.SRCALPHA)
    outline = []
    for index in range(points * 2):
        angle = TOP + math.pi * index / points
        r = radius_px * (1.0 if index % 2 == 0 else inner)
        outline.append((center + math.cos(angle) * r, center + math.sin(angle) * r))
    pygame.draw.polygon(surface, color, outline)
    if edge is not None:
        pygame.draw.polygon(surface, edge, outline, 3)
    return surface


# Hands


def line_hand(normalized, palm_px, color, finger_tints=None):
    """A hand as a line drawing: the palm and each finger outlined in ink and filled with paper (or a tint),
    drawn farthest first so fingers folded toward the viewer sit over the palm. Returns (surface, wrist)."""
    edge_px = max(2, round(palm_px * 0.045))
    pad_px = int(palm_px * 0.5) + edge_px * 2
    points = normalized[:, :2] * palm_px
    origin = points.min(axis=0) - pad_px
    size = (points.max(axis=0) - origin + pad_px).astype(int)
    xy = [tuple(p) for p in (points - origin).tolist()]
    depth = normalized[:, 2] if normalized.shape[1] > 2 else np.zeros(len(normalized))
    surface = pygame.Surface(size, pygame.SRCALPHA)
    ink = (*color, 255)
    # Farthest first; in hand coordinates a larger z is farther from the viewer.
    parts = [("Palm", PALM_OUTLINE)] + list(FINGERS.items())
    parts.sort(key=lambda part: -float(np.mean(depth[list(part[1])])))
    for name, joints in parts:
        fill = (*finger_tints[name][:3], 255) if finger_tints and name in finger_tints else (*theme.PAPER, 255)
        if name == "Palm":
            outline = [xy[j] for j in joints]
            pygame.draw.polygon(surface, fill, outline)
            pygame.draw.lines(surface, ink, True, outline, edge_px)
            for point in outline:
                pygame.draw.circle(surface, ink, point, edge_px // 2)
            continue
        width_px = max(4, int(palm_px * (theme.THUMB_WIDTH_PALMS if name == "Thumb" else theme.FINGER_WIDTH_PALMS)))
        chain = [xy[j] for j in joints]
        for layer_color, layer_px in ((ink, width_px + edge_px * 2), (fill, width_px)):
            for start, end in zip(chain, chain[1:]):
                pygame.draw.line(surface, layer_color, start, end, layer_px)
            for point in chain:
                pygame.draw.circle(surface, layer_color, point, layer_px // 2)
    return surface, (-origin).tolist()
