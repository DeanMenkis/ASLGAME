"""Capture tool that records sign templates into data/signs."""

from aslgame.runtime import Runtime  # First, so pygame loads before OpenCV.

import argparse
import time
from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from aslgame import config, theme
from aslgame.matching.normalize import normalize
from aslgame.presentation.draw import draw_hand, draw_ring, draw_text_centered
from aslgame.signs import save_sign

RING_CENTER_PX = (theme.MARGIN_PX + theme.RING_RADIUS_PX, theme.MARGIN_PX + theme.RING_RADIUS_PX)


class CaptureState(Enum):
    IDLE = auto()
    COUNTDOWN = auto()
    RECORDING = auto()


@dataclass
class Capture:
    state: CaptureState = CaptureState.IDLE
    countdown_ends_s: float = 0.0
    last_result_version: int = 0
    burst: list = field(default_factory=list)
    bursts: list = field(default_factory=list)

    def sample_count(self):
        return sum(len(burst) for burst in self.bursts)


def update(capture, now_s, pressed_key, result_version, hand):
    """The capture state machine. All transitions happen here."""
    if capture.state == CaptureState.IDLE:
        if pressed_key == pygame.K_SPACE:
            capture.state = CaptureState.COUNTDOWN
            capture.countdown_ends_s = now_s + config.CAPTURE_COUNTDOWN_S
        elif pressed_key == pygame.K_BACKSPACE and capture.bursts:
            capture.bursts.pop()
    elif capture.state == CaptureState.COUNTDOWN:
        if now_s >= capture.countdown_ends_s:
            capture.state = CaptureState.RECORDING
            capture.burst = []
            capture.last_result_version = result_version
    elif capture.state == CaptureState.RECORDING:
        # Only new tracking results count, so one frame is never recorded twice.
        if hand is not None and result_version != capture.last_result_version:
            capture.burst.append(normalize(hand.points_px, hand.is_left))
            capture.last_result_version = result_version
        if len(capture.burst) >= config.CAPTURE_SAMPLES_PER_BURST:
            capture.bursts.append(capture.burst)
            capture.state = CaptureState.IDLE


def draw(screen, capture, now_s, label, count_surface):
    if capture.state == CaptureState.COUNTDOWN:
        remaining = (capture.countdown_ends_s - now_s) / config.CAPTURE_COUNTDOWN_S
        draw_ring(screen, RING_CENTER_PX, max(1, int(theme.RING_RADIUS_PX * remaining)), 1.0, theme.ACCENT)
    elif capture.state == CaptureState.RECORDING:
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, 1.0, theme.INK_DIM)
        fraction = len(capture.burst) / config.CAPTURE_SAMPLES_PER_BURST
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, fraction, theme.ACCENT)
    else:
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, 1.0, theme.INK_DIM)
    draw_text_centered(screen, label, RING_CENTER_PX)
    count_x_px = RING_CENTER_PX[0] + theme.RING_RADIUS_PX + theme.GRID_PX * 2
    screen.blit(count_surface, (count_x_px, RING_CENTER_PX[1] - count_surface.get_height() // 2))


def main():
    parser = argparse.ArgumentParser(description="Record templates for one sign.")
    parser.add_argument("name", help="sign name, for example A")
    name = parser.parse_args().name

    runtime = Runtime(f"{config.WINDOW_TITLE} capture {name}")
    label = runtime.fonts.large.render(name, True, theme.PAPER)
    capture = Capture()
    shown_count = -1
    count_surface = None
    running = True
    while running:
        pressed_key = None
        for event in pygame.event.get():
            if runtime.handle_common(event):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN:
                pressed_key = event.key
        runtime.begin_frame()
        now_s = time.perf_counter()
        hand = runtime.result.hand if runtime.result else None
        update(capture, now_s, pressed_key, runtime.result_version, hand)
        if hand is not None:
            draw_hand(runtime.screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
        if capture.sample_count() != shown_count:
            shown_count = capture.sample_count()
            count_surface = runtime.fonts.small.render(str(shown_count), True, theme.PAPER)
        draw(runtime.screen, capture, now_s, label, count_surface)
        runtime.end_frame()
    runtime.close()

    # Saved after the loop so the frame loop never touches the disk.
    samples = [sample for burst in capture.bursts for sample in burst]
    if samples:
        total = save_sign(config.SIGNS_DIR, name, samples)
        print(f"Saved {len(samples)} samples to {config.SIGNS_DIR / name}.json ({total} total)")


if __name__ == "__main__":
    main()
