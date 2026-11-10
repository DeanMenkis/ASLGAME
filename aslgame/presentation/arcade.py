"""Play feedback in ink and fire: splats, seal stamps, banners, the score and multiplier, and the heat that drives the fire.

Heat follows the multiplier. It climbs through embers, flames, and ablaze, and a miss puts the fire out.
"""

import math

import numpy as np
import pygame

from aslgame import config, theme
from aslgame.game.scoring import EventKind, Judgement
from aslgame.presentation import ink

STAMP_TEXT = {Judgement.PERFECT: "PERFECT", Judgement.GOOD: "GOOD", Judgement.OK: "OK", Judgement.MISS: "MISS"}
STAMP_ANGLES = (7, -5, 11, -9)
SPLAT_VARIANTS = 6
HEAT_BUCKETS = 10


def heat_target(multiplier):
    span = config.FIRE_FULL_MULT - config.FIRE_START_MULT
    return min(1.0, max(0.0, (multiplier - config.FIRE_START_MULT) / span))


def stage_of(heat):
    """0 cold ink, 1 embers, 2 flames, 3 ablaze."""
    return sum(heat >= threshold for threshold in config.HEAT_STAGES)


class ArcadeFx:
    def __init__(self, fonts, size_px, settings, sfx):
        self._size_px = size_px
        self._settings = settings
        self._sfx = sfx
        self.heat = 0.0
        self.ash = 0.0
        self._stage = 0
        self._ash_s = -10.0
        self._multiplier = 1.0
        self.fire = ink.Fire(size_px)
        self._vignettes = ink.vignettes(size_px)
        serif = theme.SERIF_FAMILIES
        self._pop_font = pygame.font.SysFont(serif, 38, italic=True)
        self._stamp_font = pygame.font.SysFont(serif, 30, italic=True)
        self._banner_font = pygame.font.SysFont(serif, 132, bold=True, italic=True)
        self._word_font = pygame.font.SysFont(serif, 56, italic=True)
        self._score_font = pygame.font.SysFont(serif, 40)
        self._mult_font = pygame.font.SysFont(serif, 64, italic=True)
        self._mult_hot_font = pygame.font.SysFont(serif, 88, bold=True, italic=True)
        self._stamps = {}
        self._splats = {}
        self._under = []  # (surface, center, born_s, life_s): splats, drawn under the hand
        self._over = []  # (surface, center, born_s, life_s, rise_px, slam): stamps, pops, banners
        self._ripples = []  # (center, radius, born_s)
        self._drops = np.zeros((0, 5))  # x, y, vx, vy, born
        self._drop_color = theme.INK_BLACK
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
    def fire_on(self):
        return self._settings.fire

    # Events

    def event(self, event, center, radius_px, now_s):
        color = ink.heat_color(self.heat)
        if event.kind == EventKind.HIT:
            self._splat(center, radius_px, color, now_s)
            self._stamp(event.judgement, center, radius_px, now_s)
            text = f"+{event.points:,}" + ("  on beat" if event.on_beat else "")
            self._over.append((ink.halo_text(self._pop_font, text, color), (center[0] + radius_px * 0.95, center[1] - radius_px * 0.4),
                               now_s, config.POP_LIFE_S, theme.GRID_PX * 4, False))
            self._drip(center, color, 6 + event.tier, now_s)
            if self.fire_on and self.heat > 0.3:
                self.fire.emit([center], 8 + 24 * self.heat, now_s, self._temp(), ink.SPARK, (120, 340), (3, 6), (0.4, 0.9), 10)
            if event.combo in config.COMBO_MILESTONES:
                self._banner(f"{event.combo} combo", color, self._size_px[1] // 3, now_s)
        elif event.kind == EventKind.MISS:
            self._stamp(Judgement.MISS, center, radius_px, now_s)
            if self.heat >= config.HEAT_STAGES[0]:
                self._put_out(now_s, center)
        elif event.kind == EventKind.TIER_UP:
            self._banner(f"×{event.tier}", ink.heat_color(heat_target(event.multiplier)), self._size_px[1] // 3, now_s,
                         hot=heat_target(event.multiplier) >= config.HEAT_STAGES[1])
            if self.fire_on and self.heat > 0.2:
                self.fire.emit([center], 30 + 40 * self.heat, now_s, self._temp(), ink.SPARK, (160, 420), (3, 7), (0.5, 1.1), 14)
            self._shake(now_s, 3 + event.tier)
        elif event.kind == EventKind.BREAK:
            self._banner(f"×{event.tier} out", theme.JUDGEMENT_COLORS["MISS"], self._size_px[1] // 3, now_s)
        elif event.kind == EventKind.WORD:
            self._over.append((ink.halo_text(self._word_font, f"{event.word.lower()}  +{event.points:,}", color, halo_px=4),
                               (self._size_px[0] // 2, int(self._size_px[1] * 0.24)), now_s, config.WORD_BANNER_LIFE_S, theme.GRID_PX * 2, True))
        elif event.kind == EventKind.LOCK:
            self._ripples.append((center, radius_px * 0.5, now_s))

    def _put_out(self, now_s, center):
        """A miss snuffs the fire: hiss, smoke, ash, and the camera drains to grey for a moment."""
        strength = self.heat
        self.ash = max(self.ash, 0.4 + 0.6 * strength)
        self._ash_s = now_s
        self.heat = 0.0
        self._stage = 0
        if self.fire_on:
            extra = [center]
            if self.multiplier_rect.width:
                extra.append(self.multiplier_rect.center)
            self.fire.extinguish(strength, now_s, extra)
        self._sfx.play("hiss")

    def _temp(self):
        """Flame temperature: heat, pushed to blue-white at the multiplier cap."""
        return 1.0 if self._multiplier >= config.BLUE_FIRE_MULT else min(0.95, self.heat)

    def _splat(self, center, radius_px, color, now_s):
        variant = int(self._rng.integers(SPLAT_VARIANTS))
        key = (variant, color)
        if key not in self._splats:
            if len(self._splats) > 48:
                self._splats.clear()
            self._splats[key] = ink.make_splat(theme.GRID_PX * 7, color, variant)
        angle = self._rng.uniform(-2.6, -0.5)
        at = (center[0] + math.cos(angle) * radius_px * 1.15, center[1] + math.sin(angle) * radius_px * 1.15)
        self._under.append((self._splats[key], at, now_s, config.SPLAT_LIFE_S))

    def _stamp(self, judgement, center, radius_px, now_s):
        variant = int(self._rng.integers(len(STAMP_ANGLES)))
        key = (judgement, variant)
        if key not in self._stamps:
            self._stamps[key] = ink.make_stamp(STAMP_TEXT[judgement], self._stamp_font, theme.JUDGEMENT_COLORS[judgement.name],
                                               STAMP_ANGLES[variant], variant)
        at = (center[0] + radius_px * 0.95, center[1] - radius_px * 1.0)
        self._over.append((self._stamps[key], at, now_s, config.STAMP_LIFE_S, 0, True))

    def _banner(self, text, color, center_y, now_s, hot=False):
        if hot:
            surface = ink.fire_text(self._banner_font, text, (255, 240, 170), (210, 40, 16))
        else:
            surface = ink.halo_text(self._banner_font, text, color, halo_px=5)
        self._over = [item for item in self._over if item[1] != (self._size_px[0] // 2, center_y)]
        self._over.append((surface, (self._size_px[0] // 2, center_y), now_s, config.BANNER_LIFE_S, 0, True))

    def _drip(self, center, color, count, now_s):
        rng = self._rng
        angles = rng.uniform(-np.pi, 0, count)
        speeds = rng.uniform(120, 320, count)
        new = np.column_stack([np.full(count, center[0]), np.full(count, center[1]), np.cos(angles) * speeds,
                               np.sin(angles) * speeds, np.full(count, now_s)])
        self._drops = np.vstack([self._drops, new])
        self._drop_color = color

    def _shake(self, now_s, power):
        if self.fire_on:
            self._shake_s, self._shake_power = now_s, power

    def shake_offset(self, now_s):
        age = now_s - self._shake_s
        if age >= config.SHAKE_S:
            return (0, 0)
        power = self._shake_power * (1 - age / config.SHAKE_S)
        return (int(self._rng.uniform(-power, power)), int(self._rng.uniform(-power, power)))

    # Heat and fire

    def update(self, now_s, frame_s, multiplier):
        self._multiplier = multiplier
        target = heat_target(multiplier)
        rate = config.HEAT_RISE_PER_S if target > self.heat else config.HEAT_FALL_PER_S
        step = rate * frame_s
        self.heat = min(target, self.heat + step) if target > self.heat else max(target, self.heat - step)
        self.ash = max(0.0, self.ash - frame_s / config.ASH_S)
        stage = stage_of(self.heat)
        if stage > self._stage:
            self._sfx.play("ignite" if stage >= 2 else "ember")
        self._stage = stage
        if self.fire_on:
            self._feed_fire(now_s, frame_s)
        self.fire.update(now_s, frame_s)
        if len(self._drops):
            d = self._drops[(now_s - self._drops[:, 4]) < config.PARTICLE_LIFE_S]
            d[:, 3] += config.PARTICLE_GRAVITY * frame_s
            d[:, 0:2] += d[:, 2:4] * frame_s
            self._drops = d
        self._under = [item for item in self._under if now_s - item[2] < item[3]]
        self._over = [item for item in self._over if now_s - item[2] < item[3]]
        self._ripples = [r for r in self._ripples if now_s - r[2] < config.SHOCKWAVE_LIFE_S]

    def _feed_fire(self, now_s, frame_s):
        """The bottom edge: a breathing ember glow, then flames, then a blaze."""
        heat = self.heat
        embers, flames, ablaze = config.HEAT_STAGES
        if heat < embers:
            return
        width, height = self._size_px
        temp = self._temp()
        breathing = 0.8 + 0.2 * math.sin(now_s * 1.7)
        glow = min(1.0, (heat - embers) / (flames - embers))
        self.fire.glow_band(60 + 160 * heat, [int(c * glow * breathing * 0.9) for c in ink.lerp_color(theme.EMBER_DARK, theme.EMBER, heat)])
        bottom = [(x, height + 4) for x in np.linspace(0, width, 40)]
        self.fire.stream("sparks", bottom, config.SPARK_RATE * heat, frame_s, now_s, temp, kind=ink.SPARK,
                         speed=(40, 120 + 160 * heat), size=(3, 5), life=(0.8, 1.6), jitter_px=20)
        if heat >= flames:
            blaze = (heat - flames) / (1 - flames)
            self.fire.stream("bottom", bottom, config.FIRE_BOTTOM_RATE * (0.25 + 0.75 * blaze), frame_s, now_s, temp,
                             speed=(50 + 90 * blaze, 120 + 200 * blaze), size=(10 + 8 * blaze, 22 + 18 * blaze),
                             life=(0.3, 0.55 + 0.3 * blaze), jitter_px=14)
        if heat >= flames and self.multiplier_rect.width:
            # The burning multiplier throws sparks; the number itself stays crisp on top.
            rect = self.multiplier_rect
            points = [(x, rect.top + rect.height * 0.25) for x in np.linspace(rect.left + 10, rect.right - 10, 6)]
            self.fire.stream("multiplier", points, 15 + 45 * heat, frame_s, now_s, temp, kind=ink.HUD_SPARK, speed=(30, 110),
                             size=(2, 4), life=(0.5, 1.1), jitter_px=8)

    def burn_fuse(self, tip, center, radius_px, fraction, now_s, frame_s):
        """The fuse ring's end burns once there is heat: flames at the tip, an ember glow along the stroke."""
        if not self.fire_on or self.heat < config.HEAT_STAGES[0]:
            return
        temp = self._temp()
        self.fire.stream("tip", [tip], config.FIRE_TIP_RATE * self.heat, frame_s, now_s, temp,
                         speed=(40, 110), size=(6, 14), life=(0.25, 0.5), jitter_px=4)
        self.fire.glow_arc(center, radius_px, fraction, theme.GRID_PX * 4, [int(c * 0.5 * self.heat) for c in theme.EMBER])

    # Drawing

    def draw_backdrop(self, screen):
        self._vignettes.draw(screen, self.heat)

    def draw_under(self, canvas, now_s):
        for surface, center, born_s, life_s in self._under:
            age = (now_s - born_s) / life_s
            # Ink soaks in fast, sits, then fades.
            grow = min(1.0, 0.7 + age * 6)
            shown = pygame.transform.smoothscale_by(surface, grow) if grow < 1 else surface
            shown.set_alpha(int(235 * (1 - max(0.0, age - 0.4) / 0.6)))
            canvas.blit(shown, shown.get_rect(center=center))

    def draw_over(self, canvas, now_s):
        for center, radius, born_s in self._ripples:
            age = (now_s - born_s) / config.SHOCKWAVE_LIFE_S
            pygame.draw.circle(canvas, ink.heat_color(self.heat), center, radius * (1 + age), max(1, int(4 * (1 - age))))
        for x, y in self._drops[:, 0:2].tolist():
            pygame.draw.circle(canvas, self._drop_color, (x, y), 3)
        for surface, (x, y), born_s, life_s, rise_px, slam in self._over:
            age = (now_s - born_s) / life_s
            scale = 1.0 + 0.5 * max(0.0, 1 - (now_s - born_s) / config.SLAM_S) if slam else 1.0
            shown = pygame.transform.smoothscale_by(surface, scale) if scale > 1.001 else surface
            shown.set_alpha(int(255 * (1 - max(0.0, age - 0.6) / 0.4)))
            canvas.blit(shown, shown.get_rect(center=(x, y - rise_px * age)))

    def draw_fire_back(self, screen, now_s):
        if self.fire_on:
            self.fire.draw_back(screen, now_s)

    def draw_fire_front(self, screen, now_s):
        if self.fire_on:
            self.fire.draw_front(screen, now_s)

    def draw_hud(self, screen, score, multiplier, right_px, now_s):
        """Score in ink on the paper band; the multiplier in heated ink, burning once there are flames."""
        self._shown_score += (score - self._shown_score) * config.SCORE_ROLL_RATE
        shown = int(round(self._shown_score))
        if self._score_cache[0] != shown:
            self._score_cache = (shown, self._score_font.render(f"{shown:,}", True, theme.INK_BLACK))
        bucket = round(self.heat * HEAT_BUCKETS)
        key = (multiplier, bucket)
        if key not in self._mult_cache:
            if len(self._mult_cache) > 64:
                self._mult_cache.clear()
            text = f"×{multiplier:.1f}"
            if bucket >= config.HEAT_STAGES[1] * HEAT_BUCKETS:
                top = (190, 215, 255) if multiplier >= config.BLUE_FIRE_MULT else (255, 240, 170)
                self._mult_cache[key] = ink.fire_text(self._mult_hot_font, text, top, ink.heat_color(bucket / HEAT_BUCKETS))
            else:
                self._mult_cache[key] = self._mult_font.render(text, True, ink.heat_color(bucket / HEAT_BUCKETS))
        if multiplier != self._mult_value:
            self._mult_value = multiplier
            self._mult_changed_s = now_s
        mult = self._mult_cache[key]
        swell = max(0.0, 1 - (now_s - self._mult_changed_s) / config.PULSE_S)
        if swell > 0:
            mult = pygame.transform.smoothscale_by(mult, 1 + theme.PULSE_GROWTH * swell)
        center_y = theme.TOP_BAR_HEIGHT_PX // 2 - 4
        self.multiplier_rect = screen.blit(mult, mult.get_rect(midright=(right_px, center_y)))
        score_surface = self._score_cache[1]
        screen.blit(score_surface, score_surface.get_rect(midright=(self.multiplier_rect.left - theme.GRID_PX * 3, center_y)))
