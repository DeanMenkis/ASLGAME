"""Ink and fire: brush strokes, ink splats, seal stamps, the camera grade, and fire that grows with the multiplier.

At x1 play is quiet black ink on a sepia-washed camera. As the multiplier climbs the ink heats from black
through vermilion and ember to gold, color bleeds back into the camera, and fire rises: embers, then flames,
then ablaze, blue-white at the cap. A miss puts it out: smoke, and embers cooling into falling ash.
"""

import math
from functools import lru_cache

import numpy as np
import pygame

from aslgame import config, theme
from aslgame.hand import FINGERS, PALM_OUTLINE, WRIST

HEAT_STOPS = ((0.0, theme.INK_BLACK), (0.35, theme.SEAL), (0.7, theme.EMBER), (1.0, theme.FLAME_GOLD))
LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)
FLAME, SPARK, HUD_SPARK = 0.0, 1.0, 2.0  # HUD sparks are drawn over the paper band, sharp, with no glow


def lerp_color(a, b, t):
    t = min(1.0, max(0.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def heat_color(heat):
    """Ink color for a heat from 0 to 1: black, vermilion, ember, gold."""
    for (h0, c0), (h1, c1) in zip(HEAT_STOPS, HEAT_STOPS[1:]):
        if heat <= h1:
            return lerp_color(c0, c1, (heat - h0) / (h1 - h0))
    return HEAT_STOPS[-1][1]


def grade_matrix(heat, ash):
    """The camera grade as one 3x3 color matrix: true colour with a warm cast, richer when hot, briefly muted after a fire."""
    gray = config.GRADE_GRAY_COLD + (config.GRADE_GRAY_HOT - config.GRADE_GRAY_COLD) * heat
    gray = max(gray, ash * config.GRADE_GRAY_ASH)
    tint = lerp_color(lerp_color(theme.GRADE_COLD, theme.GRADE_HOT, heat), theme.GRADE_ASH, ash)
    mixing = (1 - gray) * np.eye(3, dtype=np.float32) + gray * np.tile(LUMA, (3, 1))
    return (np.array(tint, dtype=np.float32)[:, None] / 255.0 * mixing).astype(np.float32)


def make_vignette(size_px, color, strength, power=2.2):
    width, height = size_px
    yy, xx = np.mgrid[0:height, 0:width]
    distance = np.sqrt(((xx - width / 2) / (width / 2)) ** 2 + ((yy - height / 2) / (height / 2)) ** 2) / math.sqrt(2)
    surface = pygame.Surface(size_px, pygame.SRCALPHA)
    pygame.surfarray.pixels3d(surface)[:] = color
    pygame.surfarray.pixels_alpha(surface)[:] = np.clip(distance ** power * strength * 255, 0, 255).astype(np.uint8).T
    return surface


class Vignettes:
    """Paper at the edges when cold, a dark ember glow when hot."""

    def __init__(self, size_px):
        self._paper = make_vignette(size_px, theme.PAPER, 0.9)
        self._ember = make_vignette(size_px, theme.EMBER_DARK, 1.3)

    def draw(self, screen, heat):
        if heat < 0.98:
            self._paper.set_alpha(int(255 * (1 - heat)))
            screen.blit(self._paper, (0, 0))
        if heat > 0.02:
            self._ember.set_alpha(int(255 * heat))
            screen.blit(self._ember, (0, 0))


@lru_cache(maxsize=2)
def vignettes(size_px):
    return Vignettes(size_px)


class BrushRing:
    """A brush stroke around a circle, clockwise from the top. It lands heavy and thins; its tail splits into dry bristles.

    Drawing a smaller fraction burns the tail away first, so as a fuse it burns down from its end.
    """

    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        self._phase = rng.uniform(0, 2 * math.pi, 2)
        self._strands = rng.uniform(-0.42, 0.42, config.BRUSH_STRANDS)
        self._lengths = rng.uniform(0.35, 1.0, config.BRUSH_STRANDS)

    def _thickness(self, u, width):
        press = 0.6 + 0.4 * np.sin(np.pi * np.minimum(1.0, u * 5)) ** 0.5
        wobble = 1 + 0.08 * np.sin(u * 23 + self._phase[0]) + 0.05 * np.sin(u * 41 + self._phase[1])
        return width * press * (1 - 0.45 * u) * wobble

    @staticmethod
    def point(center, radius, fraction, start=-math.pi / 2):
        angle = start + 2 * math.pi * fraction
        return (center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius)

    def draw(self, screen, center, radius, fraction, width, color, start=-math.pi / 2):
        if fraction <= 0.01:
            return
        dry = config.BRUSH_DRY_FROM
        solid_end = min(fraction, dry)
        u = np.linspace(0.0, solid_end, max(6, int(config.BRUSH_STEPS * solid_end)))
        angles = start + 2 * np.pi * u
        half = self._thickness(u, width) / 2
        cos, sin = np.cos(angles), np.sin(angles)
        outer = np.stack([center[0] + cos * (radius + half), center[1] + sin * (radius + half)], axis=1)
        inner = np.stack([center[0] + cos * (radius - half), center[1] + sin * (radius - half)], axis=1)
        pygame.draw.polygon(screen, color, np.vstack([outer, inner[::-1]]).tolist())
        for index in (0, -1):
            pygame.draw.circle(screen, color, (center[0] + cos[index] * radius, center[1] + sin[index] * radius), half[index])
        if fraction <= dry:
            return
        line_px = max(2, int(width * 0.12))
        for offset, length in zip(self._strands, self._lengths):
            end = min(fraction, dry + (1 - dry) * length)
            uu = np.linspace(dry - 0.02, end, max(3, int(config.BRUSH_STEPS * (end - dry + 0.02))))
            aa = start + 2 * np.pi * uu
            rr = radius + offset * self._thickness(uu, width)
            pygame.draw.lines(screen, color, False, np.stack([center[0] + np.cos(aa) * rr, center[1] + np.sin(aa) * rr], axis=1).tolist(), line_px)


def make_splat(size_px, color, seed):
    """An ink splat: a pooled center, runs, and flung droplets. Made once per variant and color."""
    rng = np.random.default_rng(seed)
    dim = int(size_px * 4)
    surface = pygame.Surface((dim, dim), pygame.SRCALPHA)
    c = dim / 2
    for _ in range(22):
        angle, distance = rng.uniform(0, 2 * math.pi), abs(rng.normal(0, size_px * 0.25))
        pygame.draw.circle(surface, color, (c + math.cos(angle) * distance, c + math.sin(angle) * distance),
                           rng.uniform(size_px * 0.12, size_px * 0.3))
    for _ in range(16):
        angle = rng.uniform(0, 2 * math.pi)
        length = rng.uniform(size_px * 0.5, size_px * 1.5)
        x0, y0 = c + math.cos(angle) * size_px * 0.3, c + math.sin(angle) * size_px * 0.3
        for step in range(5):
            t = step / 5
            pygame.draw.circle(surface, color, (x0 + math.cos(angle) * length * t, y0 + math.sin(angle) * length * t),
                               size_px * 0.08 * (1 - t) + 1.2)
        tip = length * rng.uniform(1.1, 1.3)
        pygame.draw.circle(surface, color, (x0 + math.cos(angle) * tip, y0 + math.sin(angle) * tip), rng.uniform(1.5, size_px * 0.07))
    return surface


def make_stamp(text, font, color, angle, seed):
    """A seal stamp: color block, an inner rule, paper letters, and uneven pressure."""
    label = font.render(text, True, theme.PAPER)
    width, height = label.get_width() + 34, label.get_height() + 16
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, surface.get_rect(), border_radius=6)
    pygame.draw.rect(surface, theme.PAPER, surface.get_rect().inflate(-10, -10), 2, border_radius=4)
    surface.blit(label, label.get_rect(center=(width // 2, height // 2)))
    rng = np.random.default_rng(seed)
    for _ in range(width * height // 90):
        pygame.draw.circle(surface, (0, 0, 0, 0), (rng.uniform(0, width), rng.uniform(0, height)), rng.uniform(0.5, 1.8))
    return pygame.transform.rotozoom(surface, angle, 1.0)


def halo_text(font, text, color, halo=theme.PAPER, halo_px=3):
    """Text with a soft paper edge, so ink reads over any camera picture."""
    label = font.render(text, True, color)
    edge = font.render(text, True, halo)
    surface = pygame.Surface((label.get_width() + halo_px * 2, label.get_height() + halo_px * 2), pygame.SRCALPHA)
    for step in range(12):
        angle = step / 12 * 2 * math.pi
        surface.blit(edge, (halo_px + math.cos(angle) * halo_px, halo_px + math.sin(angle) * halo_px))
    surface.blit(label, (halo_px, halo_px))
    return surface


def fire_text(font, text, top, bottom, edge_px=2):
    """Text filled with a top-to-bottom gradient, for burning numbers, with a thin ink edge so it reads on paper."""
    mask = font.render(text, True, (255, 255, 255))
    gradient = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
    for y in range(mask.get_height()):
        gradient.fill((*lerp_color(top, bottom, y / max(1, mask.get_height() - 1)), 255), (0, y, mask.get_width(), 1))
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    edge = font.render(text, True, theme.INK_BLACK)
    surface = pygame.Surface((mask.get_width() + edge_px * 2, mask.get_height() + edge_px * 2), pygame.SRCALPHA)
    for step in range(12):
        angle = step / 12 * 2 * math.pi
        surface.blit(edge, (edge_px + math.cos(angle) * edge_px, edge_px + math.sin(angle) * edge_px))
    surface.blit(gradient, (edge_px, edge_px))
    return surface


def torn_band(size_px, color, seed):
    """A paper band with a torn lower edge."""
    width, height = size_px
    rng = np.random.default_rng(seed)
    points = [(0, 0), (width, 0)]
    x = width
    while x > 0:
        points.append((x, height - 8 + rng.uniform(-5, 6)))
        x -= rng.uniform(6, 18)
    points.append((0, height - 8))
    band = pygame.Surface(size_px, pygame.SRCALPHA)
    pygame.draw.polygon(band, color, points)
    return band


def draw_enso(surface, center, radius_px, width_px, seed=3):
    """A brushed circle: thick where the brush lands, thinning out, with the gap a real ensō leaves."""
    rng = np.random.default_rng(seed)
    start = -math.pi * 0.35
    sweep = math.pi * 1.86
    steps = 220
    wobble = rng.uniform(-1, 1, 6)
    for index in range(steps):
        t = index / steps
        angle = start + sweep * t
        r = radius_px * (1 + 0.025 * math.sin(angle * 3 + wobble[0]) + 0.015 * math.sin(angle * 5 + wobble[1]))
        thickness = width_px * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6) * (1 - 0.5 * t)
        x, y = center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r
        alpha = int(230 * (1 - 0.45 * t))
        pygame.draw.circle(surface, (*theme.INK_BLACK, alpha), (x, y), max(1.0, thickness / 2))
        if rng.random() < 0.35 and t > 0.5:
            # Dry brush: bristles break up near the end of the stroke.
            pygame.draw.circle(surface, (*theme.PAPER, 160), (x + rng.uniform(-thickness, thickness) / 3,
                                                            y + rng.uniform(-thickness, thickness) / 3), thickness / 6)


def draw_brush_line(surface, left, y_px, width_px, color, seed):
    """A short ink stroke used to underline a choice or a word."""
    rng = np.random.default_rng(seed)
    for index in range(width_px):
        t = index / width_px
        thickness = 7 * (1 - 0.6 * t) + rng.uniform(-0.8, 0.8)
        pygame.draw.circle(surface, color, (left + index, y_px + math.sin(t * 2.4) * 2), max(1.0, thickness / 2))


def torn_slip(size_px, color, seed):
    """A paper slip torn on all four sides, with a soft ink shadow below it. The surface is a few pixels larger than size_px."""
    width, height = size_px
    rng = np.random.default_rng(seed)

    def tear():
        bite = rng.uniform(0, 4)
        return bite + 4 if rng.random() < 0.08 else bite

    points = []
    x = 0.0
    while x < width:
        points.append((x, tear()))
        x += rng.uniform(5, 14)
    y = 0.0
    while y < height:
        points.append((width - tear(), y))
        y += rng.uniform(5, 14)
    x = float(width)
    while x > 0:
        points.append((x, height - tear()))
        x -= rng.uniform(5, 14)
    y = float(height)
    while y > 0:
        points.append((tear(), y))
        y -= rng.uniform(5, 14)
    shadow_px = 4
    slip = pygame.Surface((width + shadow_px, height + shadow_px), pygame.SRCALPHA)
    pygame.draw.polygon(slip, (*theme.INK_BLACK, 60), [(px + 2, py + shadow_px) for px, py in points])
    pygame.draw.polygon(slip, color, points)
    return slip


def ink_hand(normalized, palm_px, color, finger_tints=None):
    """A hand as an ink line drawing on paper: the palm and each finger outlined in ink and filled with paper (or a tint),
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
        fill = (*finger_tints[name], 255) if finger_tints and name in finger_tints else (*theme.PAPER, 255)
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


def make_puff(radius_px):
    """A soft grey smoke puff."""
    dim = radius_px * 2
    surface = pygame.Surface((dim, dim), pygame.SRCALPHA)
    yy, xx = np.mgrid[0:dim, 0:dim]
    distance = np.sqrt((xx - radius_px) ** 2 + (yy - radius_px) ** 2) / radius_px
    pygame.surfarray.pixels3d(surface)[:] = theme.SMOKE
    pygame.surfarray.pixels_alpha(surface)[:] = (np.clip(1 - distance, 0, 1) ** 1.4 * 140).astype(np.uint8).T
    return surface


class Fire:
    """Flames and sparks on a quarter-size layer that is scaled up and added, which blurs them into glow;
    smoke and ash after the fire goes out. Glow shapes (arcs, blobs, a bottom band) are queued each frame."""

    def __init__(self, size_px):
        self._size_px = size_px
        self._scale = config.FIRE_LAYER_SCALE
        self._layer = pygame.Surface((size_px[0] // self._scale, size_px[1] // self._scale))
        # Columns: x, y, vx, vy, born, life, size, temp, kind
        self._particles = np.zeros((0, 9))
        self._smoke = np.zeros((0, 7))  # x, y, vx, vy, born, life, puff index
        self._ash = np.zeros((0, 7))  # x, y, vx, vy, born, life, phase
        self._debt = {}
        self._puffs = [make_puff(r) for r in (18, 28, 40, 56, 76)]
        self._rng = np.random.default_rng()
        self._glows = []

    def is_idle(self):
        return not len(self._particles) and not len(self._smoke) and not len(self._ash) and not self._glows

    def emit(self, points, count, now_s, temp, kind=FLAME, speed=(60, 160), size=(10, 22), life=(0.35, 0.7), jitter_px=6):
        count = min(int(count), config.FIRE_MAX_PARTICLES - len(self._particles))
        if count <= 0:
            return
        rng = self._rng
        points = np.asarray(points, dtype=float).reshape(-1, 2)
        origins = points[rng.integers(0, len(points), count)] + rng.normal(0, jitter_px, (count, 2))
        angles = -np.pi / 2 + rng.normal(0, 0.35 if kind == FLAME else 0.8, count)
        speeds = rng.uniform(*speed, count)
        new = np.column_stack([
            origins, np.cos(angles) * speeds, np.sin(angles) * speeds, np.full(count, now_s),
            rng.uniform(*life, count), rng.uniform(*size, count), np.full(count, temp), np.full(count, kind),
        ])
        self._particles = np.vstack([self._particles, new])

    def stream(self, key, points, rate_per_s, frame_s, now_s, temp, **options):
        """Emit at a steady rate across frames."""
        debt = self._debt.get(key, 0.0) + rate_per_s * frame_s
        count = int(debt)
        self._debt[key] = debt - count
        if count:
            self.emit(points, count, now_s, temp, **options)

    def glow_arc(self, center, radius, fraction, width_px, color):
        self._glows.append(("arc", center, radius, fraction, width_px, color))

    def glow_blob(self, center, radius, color):
        self._glows.append(("blob", center, radius, color))

    def glow_band(self, height_px, color):
        self._glows.append(("band", height_px, color))

    def extinguish(self, strength, now_s, extra_points=()):
        """Snuff the flames: smoke rolls up, and embers rise, cool to grey, and fall as ash."""
        rng = self._rng
        flames = self._particles[:, 8] == FLAME
        self._particles[flames, 5] = np.minimum(self._particles[flames, 5], now_s - self._particles[flames, 4] + 0.12)
        width, height = self._size_px
        sources = [(x, height - rng.uniform(0, 50)) for x in rng.uniform(0, width, int(6 + 22 * strength))]
        sources += [(x + rng.normal(0, 20), y) for x, y in extra_points for _ in range(4)]
        if sources:
            count = len(sources)
            xy = np.array(sources)
            self._smoke = np.vstack([self._smoke, np.column_stack([
                xy, rng.normal(0, 12, count), -rng.uniform(25, 70, count), np.full(count, now_s),
                config.SMOKE_LIFE_S * rng.uniform(0.7, 1.2, count), rng.integers(0, 2, count),
            ])])
        flakes = int(60 + 220 * strength)
        self._ash = np.vstack([self._ash, np.column_stack([
            rng.uniform(0, width, flakes), height - rng.uniform(0, 80 + 260 * strength, flakes), rng.normal(0, 15, flakes),
            -rng.uniform(40, 150, flakes) * (0.5 + strength), np.full(flakes, now_s),
            config.ASH_FLAKE_LIFE_S * rng.uniform(0.6, 1.1, flakes), rng.uniform(0, 2 * np.pi, flakes),
        ])])

    def update(self, now_s, frame_s):
        p = self._particles
        if len(p):
            p = p[(now_s - p[:, 4]) < p[:, 5]]
            flames = p[:, 8] == FLAME
            p[:, 3] -= np.where(flames, config.FIRE_BUOYANCY, config.FIRE_BUOYANCY * 0.3) * frame_s
            p[:, 2] += np.sin(now_s * 7 + p[:, 1] * 0.05) * 40 * frame_s
            p[:, 0:2] += p[:, 2:4] * frame_s
            self._particles = p
        if len(self._smoke):
            s = self._smoke[(now_s - self._smoke[:, 4]) < self._smoke[:, 5]]
            s[:, 0:2] += s[:, 2:4] * frame_s
            self._smoke = s
        if len(self._ash):
            a = self._ash[(now_s - self._ash[:, 4]) < self._ash[:, 5]]
            a[:, 3] += 70 * frame_s  # rising heat gives way to gravity
            a[:, 3] = np.minimum(a[:, 3], 60)
            a[:, 0] += (a[:, 2] + np.sin(now_s * 2.5 + a[:, 6]) * 25) * frame_s
            a[:, 1] += a[:, 3] * frame_s
            self._ash = a

    def draw_back(self, screen, now_s):
        """Flames, sparks, and glow, behind the hand, the ring, and the word tiles."""
        self._draw_glow(screen, now_s)

    def draw_front(self, screen, now_s):
        """Sparks off the multiplier, then smoke and ash, over everything."""
        p = self._particles
        if len(p):
            hud = p[p[:, 8] == HUD_SPARK]
            for x, y, born, life in hud[:, [0, 1, 4, 5]].tolist():
                age = (now_s - born) / life
                pygame.draw.circle(screen, lerp_color(theme.SPARK, theme.EMBER, age), (x, y), 2.2 * (1 - age) + 0.8)
        self._draw_smoke(screen, now_s)
        self._draw_ash(screen, now_s)

    def _draw_glow(self, screen, now_s):
        p = self._particles
        if len(p):
            p = p[p[:, 8] != HUD_SPARK]
        if not len(p) and not self._glows:
            return
        scale = self._scale
        layer = self._layer
        layer.fill((0, 0, 0))
        for glow in self._glows:
            if glow[0] == "arc":
                _, center, radius, fraction, width_px, color = glow
                rect = pygame.Rect(0, 0, radius * 2 / scale, radius * 2 / scale)
                rect.center = (center[0] / scale, center[1] / scale)
                pygame.draw.arc(layer, color, rect, math.pi / 2 - 2 * math.pi * fraction, math.pi / 2, max(1, int(width_px / scale)))
            elif glow[0] == "blob":
                _, center, radius, color = glow
                pygame.draw.circle(layer, color, (center[0] / scale, center[1] / scale), radius / scale)
            else:
                _, height_px, color = glow
                rows = max(1, int(height_px / scale))
                for row in range(rows):
                    fade = (1 - row / rows) ** 2
                    layer.fill([int(c * fade) for c in color], (0, layer.get_height() - 1 - row, layer.get_width(), 1))
        self._glows.clear()
        sparks = []
        if len(p):
            age = np.clip((now_s - p[:, 4]) / p[:, 5], 0, 1)
            cores = np.stack([np.interp(p[:, 7], [s[0] for s in theme.FLAME_CORES], [s[1][i] for s in theme.FLAME_CORES])
                              for i in range(3)], axis=1)
            body = np.array(theme.FLAME_BODY, dtype=float)
            early = np.clip(age / 0.3, 0, 1)[:, None]
            late = np.clip((age - 0.3) / 0.7, 0, 1)[:, None]
            colors = np.where(age[:, None] < 0.3, cores * (1 - early) + body * early, body * (1 - late) + np.array(theme.FLAME_OUTER) * late)
            colors *= ((1 - age) ** 1.3 * 0.75)[:, None]
            radii = p[:, 6] * (1 - age) ** 0.8 / scale
            is_spark = p[:, 8] == SPARK
            colors[is_spark] = np.array(theme.SPARK) * (1 - age[is_spark])[:, None]
            radii[is_spark] = p[is_spark, 6] / scale
            for x, y, radius, color, spark in zip((p[:, 0] / scale).tolist(), (p[:, 1] / scale).tolist(), radii.tolist(),
                                                  colors.astype(int).tolist(), is_spark.tolist()):
                if spark:
                    pygame.draw.circle(layer, color, (x, y), max(0.6, radius))
                else:
                    # A tongue: narrow and tall, so a row of them reads as fire, not as glowing dots.
                    radius = max(0.8, radius)
                    pygame.draw.ellipse(layer, color, (x - radius * 0.6, y - radius * 1.4, radius * 1.2, radius * 2.8))
            sparks = p[is_spark][:, 0:2].tolist()
        screen.blit(pygame.transform.smoothscale(layer, self._size_px), (0, 0), special_flags=pygame.BLEND_ADD)
        # Sparks are also drawn sharp, so they read as sparks and not just glow.
        for x, y in sparks:
            pygame.draw.circle(screen, theme.SPARK, (x, y), 1.5)

    def _draw_smoke(self, screen, now_s):
        for x, y, _, _, born, life, puff in self._smoke.tolist():
            age = (now_s - born) / life
            sprite = self._puffs[min(len(self._puffs) - 1, int(puff) + int(age * 3))]
            sprite.set_alpha(int(255 * math.sin(math.pi * min(1.0, age * 1.2)) * 0.9))
            screen.blit(sprite, sprite.get_rect(center=(x, y)))

    def _draw_ash(self, screen, now_s):
        for x, y, _, _, born, life, phase in self._ash.tolist():
            age = (now_s - born) / life
            # Glowing embers cool to grey ash within the first part of their life, then shrink away.
            color = lerp_color(theme.FLAME_GOLD, theme.EMBER, age * 8) if age < 0.12 else lerp_color(theme.EMBER, theme.ASH, (age - 0.12) * 4)
            size = 4 if age < 0.5 else 3
            screen.fill(color, (x, y, size, max(1, size - 1 + int(math.sin(phase + now_s * 4) > 0))))
