"""Arcade feedback: score pops, particle bursts, a pulsing multiplier, a rolling score, and combo banners."""

import numpy as np
import pygame

from aslgame import config, theme


class ArcadeFx:
    def __init__(self, fonts, size_px):
        self._fonts = fonts
        self._size_px = size_px
        self._pops = []  # (surface, center, born_s)
        self._banner = None  # (surface, born_s)
        # Particles as arrays, updated with vector math: position, velocity, color index, birth time.
        self._positions = np.zeros((0, 2))
        self._velocities = np.zeros((0, 2))
        self._born = np.zeros(0)
        self._colors = []
        self._shown_score = 0.0
        self._score_surface = None
        self._score_value = -1
        self._multiplier_surface = None
        self._multiplier_value = None
        self._multiplier_changed_s = -1.0

    def hit(self, judgement_name, points, multiplier, combo, center, now_s):
        """Called once per resolved note."""
        color = theme.JUDGEMENT_COLORS[judgement_name]
        if points > 0:
            text = self._fonts.medium.render(f"+{points}", True, color)
            label = self._fonts.small.render(f"x{multiplier:.1f}", True, theme.INK)
            pop = pygame.Surface((max(text.get_width(), label.get_width()), text.get_height() + label.get_height()), pygame.SRCALPHA)
            pop.blit(text, text.get_rect(midtop=(pop.get_width() // 2, 0)))
            pop.blit(label, label.get_rect(midbottom=(pop.get_width() // 2, pop.get_height())))
            self._pops.append((pop, center, now_s))
            self._burst(center, color, now_s, config.PARTICLES_PER_HIT + combo // 2)
        if combo in config.COMBO_MILESTONES:
            self._banner = (self._fonts.display.render(f"{combo} COMBO", True, theme.ACCENT), now_s)

    def _burst(self, center, color, now_s, count):
        count = min(count, config.PARTICLES_MAX_BURST)
        angles = np.random.uniform(0, 2 * np.pi, count)
        speeds = np.random.uniform(config.PARTICLE_SPEED_MIN, config.PARTICLE_SPEED_MAX, count)
        self._positions = np.vstack([self._positions, np.tile(center, (count, 1))])
        self._velocities = np.vstack([self._velocities, np.stack([np.cos(angles), np.sin(angles)], axis=1) * speeds[:, None]])
        self._born = np.concatenate([self._born, np.full(count, now_s)])
        self._colors += [color] * count

    def update(self, now_s, frame_s):
        alive = now_s - self._born < config.PARTICLE_LIFE_S
        self._positions, self._velocities, self._born = self._positions[alive], self._velocities[alive], self._born[alive]
        self._colors = [color for color, keep in zip(self._colors, alive) if keep]
        self._velocities[:, 1] += config.PARTICLE_GRAVITY * frame_s
        self._positions += self._velocities * frame_s
        self._pops = [pop for pop in self._pops if now_s - pop[2] < config.POP_LIFE_S]
        if self._banner and now_s - self._banner[1] > config.BANNER_LIFE_S:
            self._banner = None

    def draw(self, screen, now_s):
        for (x_px, y_px), born_s, color in zip(self._positions.tolist(), self._born.tolist(), self._colors):
            radius = theme.PARTICLE_RADIUS_PX * (1 - (now_s - born_s) / config.PARTICLE_LIFE_S)
            pygame.draw.circle(screen, color, (x_px, y_px), max(1.0, radius))
        for surface, (x_px, y_px), born_s in self._pops:
            age = (now_s - born_s) / config.POP_LIFE_S
            surface.set_alpha(int(255 * (1 - age ** 2)))
            screen.blit(surface, surface.get_rect(center=(x_px, y_px - theme.POP_RISE_PX * age)))
        if self._banner:
            surface, born_s = self._banner
            age = (now_s - born_s) / config.BANNER_LIFE_S
            surface.set_alpha(int(255 * (1 - age ** 3)))
            screen.blit(surface, surface.get_rect(center=(self._size_px[0] // 2, self._size_px[1] // 3)))

    def draw_hud(self, screen, score, multiplier, combo, right_px, now_s):
        """Rolling score, then a multiplier that swells when it changes, right-aligned in the top bar."""
        self._shown_score += (score - self._shown_score) * config.SCORE_ROLL_RATE
        shown = int(round(self._shown_score))
        if shown != self._score_value:
            self._score_value = shown
            self._score_surface = self._fonts.medium.render(f"{shown:,}", True, theme.INK)
        if multiplier != self._multiplier_value:
            self._multiplier_value = multiplier
            self._multiplier_changed_s = now_s
            color = theme.ACCENT if multiplier > 1.0 else theme.INK_DIM
            self._multiplier_surface = self._fonts.large.render(f"x{multiplier:.1f}", True, color)
        swell = max(0.0, 1 - (now_s - self._multiplier_changed_s) / config.PULSE_S)
        mult = self._multiplier_surface
        if swell > 0:
            mult = pygame.transform.smoothscale_by(mult, 1 + theme.PULSE_GROWTH * swell)
        center_y_px = theme.TOP_BAR_HEIGHT_PX // 2
        rect = screen.blit(mult, mult.get_rect(midright=(right_px, center_y_px)))
        screen.blit(self._score_surface, self._score_surface.get_rect(midright=(rect.left - theme.GRID_PX * 3, center_y_px)))
