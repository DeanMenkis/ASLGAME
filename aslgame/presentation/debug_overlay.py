"""On-screen FPS and tracking latency readout."""

import pygame

from aslgame import config, theme


class DebugOverlay:
    def __init__(self, font):
        self.visible = config.DEBUG_OVERLAY_ON_START
        self._font = font
        self._panel = None
        self._next_refresh_s = 0.0
        self._worst_frame_ms = 0.0

    def toggle(self):
        self.visible = not self.visible

    def update(self, now_s, frame_interval_ms, loop_fps, camera_fps, tracker_fps, result):
        # Text is re-rendered a few times a second, not every frame.
        self._worst_frame_ms = max(self._worst_frame_ms, frame_interval_ms)
        if not self.visible or now_s < self._next_refresh_s:
            return
        self._next_refresh_s = now_s + config.DEBUG_REFRESH_S
        lines = [
            f"FPS {loop_fps:.0f}   worst frame {self._worst_frame_ms:.0f} ms",
            f"camera {camera_fps:.0f}   tracker {tracker_fps:.0f}",
        ]
        if result is not None:
            latency_ms = (result.finished_s - result.captured_s) * 1000
            age_ms = (now_s - result.captured_s) * 1000
            lines.append(f"infer {result.inference_ms:.0f} ms   latency {latency_ms:.0f} ms   age {age_ms:.0f} ms")
        self._worst_frame_ms = 0.0
        self._render(lines)

    def draw(self, screen):
        if not self.visible or self._panel is None:
            return
        screen.blit(self._panel, (theme.MARGIN_PX, screen.get_height() - theme.MARGIN_PX - self._panel.get_height()))

    def _render(self, lines):
        surfaces = [self._font.render(line, True, theme.PAPER) for line in lines]
        line_height_px = self._font.get_linesize()
        width_px = max(surface.get_width() for surface in surfaces) + theme.GRID_PX * 2
        height_px = line_height_px * len(surfaces) + theme.GRID_PX * 2
        if self._panel is None or self._panel.get_size() != (width_px, height_px):
            self._panel = pygame.Surface((width_px, height_px), pygame.SRCALPHA)
        self._panel.fill((*theme.BLUE, 225))
        for row, surface in enumerate(surfaces):
            self._panel.blit(surface, (theme.GRID_PX, theme.GRID_PX + row * line_height_px))
