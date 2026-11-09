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
    body: pygame.font.Font
    medium: pygame.font.Font
    large: pygame.font.Font
    display: pygame.font.Font
    serif_body: pygame.font.Font
    serif_mode: pygame.font.Font
    serif_title: pygame.font.Font


def make_fonts():
    return Fonts(
        small=pygame.font.SysFont(theme.FONT_FAMILIES, theme.FONT_SIZE_SMALL_PX),
        body=pygame.font.SysFont(theme.FONT_FAMILIES, theme.FONT_SIZE_BODY_PX),
        medium=pygame.font.SysFont(theme.FONT_FAMILIES, theme.FONT_SIZE_MEDIUM_PX, bold=True),
        large=pygame.font.SysFont(theme.FONT_FAMILIES, theme.FONT_SIZE_LARGE_PX, bold=True),
        display=pygame.font.SysFont(theme.FONT_FAMILIES, theme.FONT_SIZE_DISPLAY_PX, bold=True),
        serif_body=pygame.font.SysFont(theme.SERIF_FAMILIES, theme.FONT_SIZE_BODY_PX),
        serif_mode=pygame.font.SysFont(theme.SERIF_FAMILIES, theme.FONT_SIZE_SERIF_MODE_PX),
        serif_title=pygame.font.SysFont(theme.SERIF_FAMILIES, theme.FONT_SIZE_SERIF_TITLE_PX, italic=True),
    )


def fit_window(size_px):
    """Grow the window to fill most of the screen at the same aspect. Skipped if SDL cannot resize it."""
    desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
    scale = min(desktop_w * config.WINDOW_SCREEN_FRACTION / size_px[0], desktop_h * config.WINDOW_SCREEN_FRACTION / size_px[1])
    if scale <= 1:
        return
    try:
        from pygame._sdl2.video import WINDOWPOS_CENTERED, Window
        window = Window.from_display_module()
        window.size = (int(size_px[0] * scale), int(size_px[1] * scale))
        window.position = WINDOWPOS_CENTERED
    except (ImportError, AttributeError, pygame.error):
        return


class Runtime:
    def __init__(self, title):
        pygame.mixer.pre_init(config.AUDIO_RATE_HZ, config.AUDIO_SAMPLE_BITS, config.AUDIO_CHANNELS, config.AUDIO_BUFFER_SAMPLES)
        pygame.init()
        self.camera = Camera()
        self.tracker = Tracker(self.camera.frames)
        # SCALED keeps a fixed drawing size and lets the window grow, so layout and mouse positions never change.
        self.screen = pygame.display.set_mode(self.camera.size_px, pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(title)
        fit_window(self.camera.size_px)
        self.fonts = make_fonts()
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
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            pygame.display.toggle_fullscreen()
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
