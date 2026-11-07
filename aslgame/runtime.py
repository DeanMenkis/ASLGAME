"""Window, background threads, and frame pacing shared by every pygame entry point."""

import os
import time
from dataclasses import dataclass

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

# pygame must load before OpenCV: both bundle SDL2, and the first copy loaded wins on macOS.
import pygame  # noqa: E402

from aslgame import config, theme  # noqa: E402
from aslgame.capture.camera import Camera  # noqa: E402
from aslgame.fps import smooth_fps  # noqa: E402
from aslgame.presentation.debug_overlay import DebugOverlay  # noqa: E402
from aslgame.presentation.draw import draw_camera  # noqa: E402
from aslgame.tracking.tracker import Tracker  # noqa: E402


@dataclass(frozen=True)
class Fonts:
    small: pygame.font.Font
    medium: pygame.font.Font
    large: pygame.font.Font


class Runtime:
    def __init__(self, title):
        pygame.mixer.pre_init(config.AUDIO_RATE_HZ, config.AUDIO_SAMPLE_BITS, config.AUDIO_CHANNELS, config.AUDIO_BUFFER_SAMPLES)
        pygame.init()
        self.camera = Camera()
        self.tracker = Tracker(self.camera.frames)
        self.screen = pygame.display.set_mode(self.camera.size_px)
        pygame.display.set_caption(title)
        self.fonts = Fonts(
            small=pygame.font.Font(theme.FONT_NAME, theme.FONT_SIZE_SMALL_PX),
            medium=pygame.font.Font(theme.FONT_NAME, theme.FONT_SIZE_MEDIUM_PX),
            large=pygame.font.Font(theme.FONT_NAME, theme.FONT_SIZE_LARGE_PX),
        )
        self.debug = DebugOverlay(self.fonts.small)
        self.clock = pygame.time.Clock()
        self.fps = 0.0
        self.frame = None
        self.result = None
        self.result_version = 0
        self._frame_interval_ms = 0.0
        self.camera.start()
        self.tracker.start()

    def begin_frame(self):
        """Take the newest frame and tracking result. Never waits."""
        _, self.frame = self.camera.frames.get()
        self.result_version, self.result = self.tracker.results.get()
        self.screen.fill(theme.BACKGROUND)
        if self.frame is not None:
            draw_camera(self.screen, self.frame)

    def handle_common(self, event):
        """Handle events every screen shares. Return True when the window is closed."""
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.debug.toggle()
        return False

    def end_frame(self):
        now_s = time.perf_counter()
        self.debug.update(now_s, self._frame_interval_ms, self.fps, self.camera.fps, self.tracker.fps, self.result)
        self.debug.draw(self.screen)
        pygame.display.flip()
        self._frame_interval_ms = self.clock.tick(config.TARGET_FPS)
        self.fps = smooth_fps(self.fps, self._frame_interval_ms / 1000)

    def close(self):
        self.tracker.stop()
        self.camera.stop()
        pygame.quit()
