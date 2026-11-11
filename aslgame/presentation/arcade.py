"""Play feedback from the press: dot bursts, judgement labels, overprinted banners, the score and multiplier, and heat.

Heat follows the multiplier. It adds the yellow plate to the camera print, raises halftone dots from the bottom edge,
and throws paper chads. A miss slips the plates out of register and the heat is gone.
"""

import math

import numpy as np
import pygame

from aslgame import config, theme
from aslgame.game.scoring import EventKind, Judgement
from aslgame.presentation import press

STAMP_TEXT = {Judgement.PERFECT: "PERFECT", Judgement.GOOD: "GOOD", Judgement.OK: "OK", Judgement.MISS: "MISS"}
STAMP_ANGLES = (7, -5, 11, -9)
BURST_DOTS = 18
BURST_LIFE_S = 0.45
CHAD_INKS = (theme.RED, theme.YELLOW, theme.BLUE, theme.PAPER)
BANNER_SHIFT_PX = (8, 8)


def heat_target(multiplier):
    span = config.HEAT_FULL_MULT - config.HEAT_START_MULT
    return min(1.0, max(0.0, (multiplier - config.HEAT_START_MULT) / span))


def stage_of(heat):
    """0 cold, 1 warm, 2 hot, 3 full colour."""
    return sum(heat >= threshold for threshold in config.HEAT_STAGES)


class ArcadeFx:
    def __init__(self, fonts, size_px, settings, sfx):
        self._size_px = size_px
        self._settings = settings
        self._sfx = sfx
        self.heat = 0.0
        self.slip = 0.0  # how far the plates are out of register after a miss, 1 to 0
        self._field = 0.0  # how high the dots at the bottom stand, 0 to 1
        self._stage = 0
        self._multiplier = 1.0
        slab, label = theme.SLAB_FAMILIES, theme.LABEL_FAMILIES
        self._pop_font = pygame.font.SysFont(slab, 34, bold=True)
        self._stamp_font = pygame.font.SysFont(label, 34, bold=True)
        self._banner_font = pygame.font.SysFont(slab, 124, bold=True)
        self._word_font = pygame.font.SysFont(slab, 60, bold=True)
        self._score_font = pygame.font.SysFont(label, 46, bold=True)
        self._mult_font = pygame.font.SysFont(slab, 58, bold=True)
        field_px = (size_px[0], config.DOT_FIELD_HEIGHT_PX)
        pitch = config.DOT_FIELD_PITCH_PX
        self._fields = [press.dot_field(field_px, pitch, theme.RED), press.dot_field(field_px, pitch, theme.YELLOW, 0.9),
                        press.dot_field(field_px, pitch * 2, theme.BLUE, 0.5)]
        self._star = press.starburst(theme.GRID_PX * 9, 14, theme.YELLOW)
        self._stamps = {}
        self._bursts = []  # (center, radius, born_s, color): dots thrown out from the hand, under it
        self._over = []  # (surface, center, born_s, life_s, rise_px, slam): labels, pops, banners
        self._ripples = []  # (center, radius, born_s)
        self._chads = np.zeros((0, 9))  # x, y, vx, vy, born, life, size, ink index, gravity
        self._chad_debt = 0.0
        self._rng = np.random.default_rng()
        self._shake_s = -1.0
        self._shake_power = 0.0
        self._shown_score = 0.0
        self._score_cache = (None, None)
        self._mult_cache = {}
        self._mult_value = None
        self._mult_changed_s = -1.0
        self.multiplier_rect = pygame.Rect(0, 0, 0, 0)

    @property
    def motion_on(self):
        return self._settings.motion

    # Events

    def event(self, event, center, radius_px, now_s):
        color = press.heat_color(self.heat)
        banner_y = self._size_px[1] // 3
        if event.kind == EventKind.HIT:
            self._bursts.append((center, radius_px, now_s, color))
            self._stamp(event.judgement, center, radius_px, now_s)
            text = f"+{event.points:,}" + ("  ON BEAT" if event.on_beat else "")
            self._over.append((press.halo_text(self._pop_font, text, color), (center[0] + radius_px * 0.95, center[1] - radius_px * 0.4),
                               now_s, config.POP_LIFE_S, theme.GRID_PX * 4, False))
            if self.motion_on and self.heat > 0.3:
                self._throw(center, 6 + 16 * self.heat, now_s)
            if event.combo in config.COMBO_MILESTONES:
                self._banner(f"{event.combo} COMBO", theme.BLUE, theme.RED, banner_y, now_s)
        elif event.kind == EventKind.MISS:
            self._stamp(Judgement.MISS, center, radius_px, now_s)
            if self.heat >= config.HEAT_STAGES[0]:
                self._misprint(now_s)
        elif event.kind == EventKind.TIER_UP:
            hot = heat_target(event.multiplier) >= config.HEAT_STAGES[1]
            self._banner(f"×{event.tier}", theme.RED if hot else theme.BLUE, theme.YELLOW if hot else theme.RED, banner_y, now_s)
            if self.motion_on:
                self._throw(center, 14 + 5 * event.tier, now_s)
                self._shake_s, self._shake_power = now_s, 3 + event.tier
        elif event.kind == EventKind.BREAK:
            self._banner(f"×{event.tier} OUT", theme.JUDGEMENT_COLORS["MISS"], theme.PAPER_SHADE, banner_y, now_s)
        elif event.kind == EventKind.WORD:
            # A clean word is pulled off the press: set in type, with what it paid.
            surface = press.overprint_text(self._word_font, f"{event.word}  +{event.points:,}", theme.BLUE, theme.RED, (4, 4), halo_px=4)
            self._over.append((surface, (self._size_px[0] // 2, int(self._size_px[1] * 0.24)), now_s, config.WORD_BANNER_LIFE_S,
                               theme.GRID_PX * 2, True))
        elif event.kind == EventKind.LOCK:
            self._ripples.append((center, radius_px * 0.5, now_s))

    def _misprint(self, now_s):
        """A miss: the plates slip, the yellow drops out, and the dots fall away."""
        self.slip = max(self.slip, 0.4 + 0.6 * self.heat) if self.motion_on else 0.0
        self.heat = 0.0
        self._stage = 0
        self._sfx.play("hiss")

    def _stamp(self, judgement, center, radius_px, now_s):
        variant = int(self._rng.integers(len(STAMP_ANGLES)))
        key = (judgement, variant)
        if key not in self._stamps:
            name = judgement.name
            self._stamps[key] = press.make_stamp(STAMP_TEXT[judgement], self._stamp_font, theme.JUDGEMENT_COLORS[name],
                                                 theme.JUDGEMENT_TEXT_COLORS[name], STAMP_ANGLES[variant])
        at = (center[0] + radius_px * 0.95, center[1] - radius_px * 1.0)
        self._over.append((self._stamps[key], at, now_s, config.STAMP_LIFE_S, 0, True))

    def _banner(self, text, front, back, center_y, now_s):
        surface = press.overprint_text(self._banner_font, text, front, back, BANNER_SHIFT_PX, halo_px=5)
        at = (self._size_px[0] // 2, center_y)
        self._over = [item for item in self._over if item[1] != at]
        self._over.append((surface, at, now_s, config.BANNER_LIFE_S, 0, True))

    def _add_chads(self, xy, velocity, now_s, life, size, gravity):
        count = min(len(xy), config.CHADS_MAX - len(self._chads))
        if count <= 0:
            return
        rng = self._rng
        new = np.column_stack([xy[:count], velocity[:count], np.full(count, now_s), rng.uniform(0.6, 1.0, count) * life,
                               rng.uniform(*size, count), rng.integers(0, len(CHAD_INKS), count), np.full(count, gravity)])
        self._chads = np.vstack([self._chads, new])

    def _throw(self, center, count, now_s):
        """Paper chads punched out by a hit: flung up and out, then falling."""
        count = int(count)
        rng = self._rng
        angles = rng.uniform(-np.pi, 0, count)
        speeds = rng.uniform(config.PARTICLE_SPEED_MIN, config.PARTICLE_SPEED_MAX, count)
        velocity = np.column_stack([np.cos(angles) * speeds, np.sin(angles) * speeds])
        self._add_chads(np.tile(np.array(center, dtype=float), (count, 1)), velocity, now_s, config.CHAD_LIFE_S, (4, 8), 1.0)

    def shake_offset(self, now_s):
        age = now_s - self._shake_s
        if age >= config.SHAKE_S:
            return (0, 0)
        power = self._shake_power * (1 - age / config.SHAKE_S)
        return (int(self._rng.uniform(-power, power)), int(self._rng.uniform(-power, power)))

    # Heat

    def update(self, now_s, frame_s, multiplier):
        self._multiplier = multiplier
        target = heat_target(multiplier)
        rate = config.HEAT_RISE_PER_S if target > self.heat else config.HEAT_FALL_PER_S
        step = rate * frame_s
        self.heat = min(target, self.heat + step) if target > self.heat else max(target, self.heat - step)
        self.slip = max(0.0, self.slip - frame_s / config.SLIP_S)
        # The dots rise with the heat and drop away fast when it is lost.
        self._field += (self.heat - self._field) * min(1.0, frame_s * (2.5 if self.heat > self._field else 9.0))
        stage = stage_of(self.heat)
        if stage > self._stage:
            self._sfx.play("ignite" if stage >= 2 else "ember")
        self._stage = stage
        if self.motion_on and stage >= 2:
            self._float_dots(now_s, frame_s)
        if len(self._chads):
            c = self._chads[(now_s - self._chads[:, 4]) < self._chads[:, 5]]
            c[:, 3] += config.PARTICLE_GRAVITY * c[:, 8] * frame_s
            c[:, 0:2] += c[:, 2:4] * frame_s
            self._chads = c
        self._bursts = [item for item in self._bursts if now_s - item[2] < BURST_LIFE_S]
        self._over = [item for item in self._over if now_s - item[2] < item[3]]
        self._ripples = [r for r in self._ripples if now_s - r[2] < config.SHOCKWAVE_LIFE_S]

    def _float_dots(self, now_s, frame_s):
        """Once hot, loose dots lift off the field at the bottom and drift up."""
        self._chad_debt += 26 * self.heat * frame_s
        count = int(self._chad_debt)
        self._chad_debt -= count
        if not count:
            return
        rng = self._rng
        width, height = self._size_px
        xy = np.column_stack([rng.uniform(0, width, count), np.full(count, height + 6.0)])
        velocity = np.column_stack([rng.normal(0, 14, count), -rng.uniform(70, 190, count)])
        self._add_chads(xy, velocity, now_s, 2.2, (3, 7), 0.0)

    # Drawing

    def draw_field(self, screen, now_s):
        """Halftone dots printed up from the bottom edge, behind the hand and the tiles: one ink when warm, more when hot."""
        if not self.motion_on or self._field < 0.02:
            return
        height = self._size_px[1]
        rise_px = config.DOT_FIELD_HEIGHT_PX * self._field
        inks = 1 + (self._stage >= 2) + (self._multiplier >= config.FULL_PRESS_MULT)
        for index in range(inks):
            # Each plate drifts a little on its own, so the inks slide over each other.
            drift = math.sin(now_s * (0.7 + 0.3 * index) + index * 2.1) * 8
            lift = rise_px * (1.0 - 0.22 * index)
            screen.blit(self._fields[index], (drift - 8, height - lift), special_flags=pygame.BLEND_RGB_MULT)

    def draw_under(self, canvas, now_s):
        for center, radius, born_s, color in self._bursts:
            age = (now_s - born_s) / BURST_LIFE_S
            reach = radius * (1.05 + 0.9 * age ** 0.6)
            dot_px = 9 * (1 - age)
            for index in range(BURST_DOTS):
                at = press.ring_point(center, reach, index / BURST_DOTS)
                pygame.draw.circle(canvas, theme.PAPER, at, dot_px + 2)
                pygame.draw.circle(canvas, color, at, dot_px)

    def draw_over(self, canvas, now_s):
        for center, radius, born_s in self._ripples:
            age = (now_s - born_s) / config.SHOCKWAVE_LIFE_S
            pygame.draw.circle(canvas, press.heat_color(self.heat), center, radius * (1 + age), max(1, int(4 * (1 - age))))
        for surface, (x, y), born_s, life_s, rise_px, slam in self._over:
            age = (now_s - born_s) / life_s
            scale = 1.0 + 0.5 * max(0.0, 1 - (now_s - born_s) / config.SLAM_S) if slam else 1.0
            shown = pygame.transform.smoothscale_by(surface, scale) if scale > 1.001 else surface
            shown.set_alpha(int(255 * (1 - max(0.0, age - 0.6) / 0.4)))
            canvas.blit(shown, shown.get_rect(center=(x, y - rise_px * age)))

    def draw_chads(self, screen, now_s):
        """Loose paper and ink dots, over everything."""
        c = self._chads
        if not len(c):
            return
        ages = np.clip((now_s - c[:, 4]) / c[:, 5], 0, 1)
        for x, y, size, ink, age in zip(c[:, 0].tolist(), c[:, 1].tolist(), c[:, 6].tolist(), c[:, 7].astype(int).tolist(), ages.tolist()):
            pygame.draw.circle(screen, CHAD_INKS[ink], (x, y), size * (1 - age * 0.7))

    def draw_hud(self, screen, score, multiplier, right_px, now_s):
        """Score in blue on the paper band; the multiplier in heated ink, overprinted once it is hot."""
        self._shown_score += (score - self._shown_score) * config.SCORE_ROLL_RATE
        shown = int(round(self._shown_score))
        if self._score_cache[0] != shown:
            self._score_cache = (shown, self._score_font.render(f"{shown:,}", True, theme.BLUE))
        key = (multiplier, self._stage)
        if key not in self._mult_cache:
            if len(self._mult_cache) > 64:
                self._mult_cache.clear()
            text = f"×{multiplier:.1f}"
            if self._stage >= 2:
                self._mult_cache[key] = press.overprint_text(self._mult_font, text, theme.RED, theme.YELLOW, (4, 4))
            else:
                self._mult_cache[key] = self._mult_font.render(text, True, press.heat_color(heat_target(multiplier)))
        if multiplier != self._mult_value:
            self._mult_value = multiplier
            self._mult_changed_s = now_s
        mult = self._mult_cache[key]
        swell = max(0.0, 1 - (now_s - self._mult_changed_s) / config.PULSE_S)
        if swell > 0:
            mult = pygame.transform.smoothscale_by(mult, 1 + theme.PULSE_GROWTH * swell)
        center_y = theme.TOP_BAR_CENTER_Y_PX
        rect = mult.get_rect(midright=(right_px, center_y))
        if multiplier >= config.FULL_PRESS_MULT:
            screen.blit(self._star, self._star.get_rect(center=rect.center))
        self.multiplier_rect = screen.blit(mult, rect)
        score_surface = self._score_cache[1]
        screen.blit(score_surface, score_surface.get_rect(midright=(self.multiplier_rect.left - theme.GRID_PX * 3, center_y)))
