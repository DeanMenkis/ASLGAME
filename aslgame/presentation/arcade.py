"""Arcade feedback: score pops, particle bursts, a tiered multiplier with embers, shockwaves, shake, and banners."""

import numpy as np
import pygame

from aslgame import config, theme
from aslgame.game.scoring import EventKind


def tier_color(tier):
    return theme.TIER_COLORS[min(tier, len(theme.TIER_COLORS)) - 1]


class ArcadeFx:
    def __init__(self, fonts, size_px):
        self._fonts = fonts
        self._size_px = size_px
        self._pops = []  # (surface, center, born_s)
        self._banners = []  # (surface, center_y, born_s, life_s)
        self._waves = []  # (center, color, born_s, start_radius)
        self._positions = np.zeros((0, 2))
        self._velocities = np.zeros((0, 2))
        self._born = np.zeros(0)
        self._life = np.zeros(0)
        self._colors = []
        self._shown_score = 0.0
        self._score_surface = None
        self._score_value = -1
        self._multiplier_surface = None
        self._multiplier_value = None
        self._multiplier_changed_s = -1.0
        self._multiplier_rect = pygame.Rect(0, 0, 0, 0)
        self._shake_s = -1.0
        self._shake_power = 0.0
        self._ember_debt = 0.0

    def event(self, event, center, radius_px, now_s):
        """Turn one scoring event into effects."""
        if event.kind == EventKind.HIT:
            color = theme.JUDGEMENT_COLORS[event.judgement.name]
            text = self._fonts.medium.render(f"+{event.points}", True, color)
            label = self._fonts.small.render(f"x{event.multiplier:.1f}", True, tier_color(event.tier))
            pop = pygame.Surface((max(text.get_width(), label.get_width()), text.get_height() + label.get_height()), pygame.SRCALPHA)
            pop.blit(text, text.get_rect(midtop=(pop.get_width() // 2, 0)))
            pop.blit(label, label.get_rect(midbottom=(pop.get_width() // 2, pop.get_height())))
            self._pops.append((pop, center, now_s))
            count = config.PARTICLES_PER_HIT + event.tier * config.PARTICLES_PER_TIER + event.combo // 4
            self._burst(center, color, now_s, count, 1.0 + 0.1 * event.tier)
            self._waves.append((center, color, now_s, radius_px))
            if event.combo in config.COMBO_MILESTONES:
                self._banner(f"{event.combo} COMBO", theme.ACCENT, self._size_px[1] // 3, now_s, config.BANNER_LIFE_S)
        elif event.kind == EventKind.TIER_UP:
            color = tier_color(event.tier)
            self._banner(f"x{event.tier}", color, self._size_px[1] // 3, now_s, config.BANNER_LIFE_S)
            self._waves.append((center, color, now_s, radius_px * 1.5))
            self._burst(center, color, now_s, config.PARTICLES_MAX_BURST, 1.6)
            self._shake(now_s, 4 + event.tier * 1.5)
        elif event.kind == EventKind.BREAK:
            self._banner(f"x{event.tier} BROKEN", theme.JUDGEMENT_COLORS["MISS"], self._size_px[1] // 3, now_s, config.BANNER_LIFE_S)
            self._shake(now_s, 10)
        elif event.kind == EventKind.WORD:
            self._banner(f"{event.word}  +{event.points:,}", theme.INK, self._size_px[1] // 2, now_s, config.WORD_BANNER_LIFE_S,
                         self._fonts.large)
        elif event.kind == EventKind.LOCK:
            self._waves.append((center, theme.ACCENT, now_s, radius_px * 0.6))

    def _banner(self, text, color, center_y, now_s, life_s, font=None):
        surface = (font or self._fonts.display).render(text, True, color)
        shadow = (font or self._fonts.display).render(text, True, theme.ACCENT_INK)
        both = pygame.Surface((surface.get_width() + 6, surface.get_height() + 6), pygame.SRCALPHA)
        both.blit(shadow, (6, 6))
        both.blit(surface, (0, 0))
        self._banners = [b for b in self._banners if b[1] != center_y]
        self._banners.append((both, center_y, now_s, life_s))

    def _shake(self, now_s, power):
        self._shake_s = now_s
        self._shake_power = max(power, self._shake_power if now_s - self._shake_s < config.SHAKE_S else 0)

    def shake_offset(self, now_s):
        age = now_s - self._shake_s
        if age >= config.SHAKE_S:
            return (0, 0)
        power = self._shake_power * (1 - age / config.SHAKE_S)
        return (int(np.random.uniform(-power, power)), int(np.random.uniform(-power, power)))

    def _burst(self, center, color, now_s, count, speed=1.0, life_s=config.PARTICLE_LIFE_S, spread=2 * np.pi, up=False):
        count = min(count, config.PARTICLES_MAX_BURST)
        if count <= 0:
            return
        angles = np.random.uniform(0, spread, count) + (-np.pi / 2 - spread / 2 if up else 0)
        speeds = np.random.uniform(config.PARTICLE_SPEED_MIN, config.PARTICLE_SPEED_MAX, count) * speed
        self._positions = np.vstack([self._positions, np.tile(center, (count, 1)) + np.random.uniform(-4, 4, (count, 2))])
        self._velocities = np.vstack([self._velocities, np.stack([np.cos(angles), np.sin(angles)], axis=1) * speeds[:, None]])
        self._born = np.concatenate([self._born, np.full(count, now_s)])
        self._life = np.concatenate([self._life, np.full(count, life_s)])
        self._colors += [color] * count

    def update(self, now_s, frame_s, multiplier):
        alive = now_s - self._born < self._life
        self._positions, self._velocities = self._positions[alive], self._velocities[alive]
        self._born, self._life = self._born[alive], self._life[alive]
        self._colors = [color for color, keep in zip(self._colors, alive) if keep]
        self._velocities[:, 1] += config.PARTICLE_GRAVITY * frame_s
        self._positions += self._velocities * frame_s
        self._pops = [pop for pop in self._pops if now_s - pop[2] < config.POP_LIFE_S]
        self._banners = [b for b in self._banners if now_s - b[2] < b[3]]
        self._waves = [w for w in self._waves if now_s - w[2] < config.SHOCKWAVE_LIFE_S]
        # Embers rise off a hot multiplier: the higher the tier, the more.
        tier = int(multiplier)
        if tier >= config.EMBER_MIN_TIER and self._multiplier_rect.width:
            self._ember_debt += frame_s * config.EMBERS_PER_TIER_PER_S * tier
            count = int(self._ember_debt)
            self._ember_debt -= count
            for _ in range(count):
                x_px = np.random.uniform(self._multiplier_rect.left, self._multiplier_rect.right)
                self._burst((x_px, self._multiplier_rect.bottom - 6), tier_color(tier), now_s, 1, 0.25, config.EMBER_LIFE_S, 0.8, True)

    def draw(self, screen, now_s):
        for center, color, born_s, start_radius in self._waves:
            age = (now_s - born_s) / config.SHOCKWAVE_LIFE_S
            width = max(1, int(theme.APPROACH_RING_LINE_PX * (1 - age)))
            pygame.draw.circle(screen, color, center, start_radius * (1 + age * 0.8), width)
        for (x_px, y_px), born_s, life_s, color in zip(self._positions.tolist(), self._born.tolist(), self._life.tolist(), self._colors):
            radius = theme.PARTICLE_RADIUS_PX * (1 - (now_s - born_s) / life_s)
            pygame.draw.circle(screen, color, (x_px, y_px), max(1.0, radius))
        for surface, (x_px, y_px), born_s in self._pops:
            age = (now_s - born_s) / config.POP_LIFE_S
            surface.set_alpha(int(255 * (1 - age ** 2)))
            screen.blit(surface, surface.get_rect(center=(x_px, y_px - theme.POP_RISE_PX * age)))
        for surface, center_y, born_s, life_s in self._banners:
            age = (now_s - born_s) / life_s
            # Slams in large, settles, then fades.
            scale = 1.0 + 0.6 * max(0.0, 1 - age * 6) ** 2
            shown = pygame.transform.smoothscale_by(surface, scale) if scale > 1.001 else surface
            shown.set_alpha(int(255 * (1 - age ** 3)))
            screen.blit(shown, shown.get_rect(center=(self._size_px[0] // 2, center_y)))

    def draw_hud(self, screen, score, multiplier, right_px, now_s):
        """Rolling score, then the multiplier, colored by its tier and swelling when it changes."""
        self._shown_score += (score - self._shown_score) * config.SCORE_ROLL_RATE
        shown = int(round(self._shown_score))
        if shown != self._score_value:
            self._score_value = shown
            self._score_surface = self._fonts.medium.render(f"{shown:,}", True, theme.INK)
        if multiplier != self._multiplier_value:
            self._multiplier_value = multiplier
            self._multiplier_changed_s = now_s
            color = tier_color(int(multiplier)) if multiplier > 1.0 else theme.INK_DIM
            self._multiplier_surface = self._fonts.large.render(f"x{multiplier:.1f}", True, color)
        swell = max(0.0, 1 - (now_s - self._multiplier_changed_s) / config.PULSE_S)
        mult = self._multiplier_surface
        if swell > 0:
            mult = pygame.transform.smoothscale_by(mult, 1 + theme.PULSE_GROWTH * swell)
        center_y_px = theme.TOP_BAR_HEIGHT_PX // 2
        self._multiplier_rect = screen.blit(mult, mult.get_rect(midright=(right_px, center_y_px)))
        screen.blit(self._score_surface, self._score_surface.get_rect(midright=(self._multiplier_rect.left - theme.GRID_PX * 3, center_y_px)))
